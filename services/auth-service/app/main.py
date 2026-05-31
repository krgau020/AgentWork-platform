"""
main.py — FastAPI application entry point for the auth service.

Role in the system:
    Bootstraps the auth service: creates the FastAPI app, registers the router,
    and wires up the startup event that waits for the database to be ready.

    In the AgentWork platform, this service runs on port 8001 (inside Docker)
    and is accessed either directly (dev testing) or through the API gateway
    on port 8000 (production traffic).

Startup sequence:
    1. Docker starts the container and runs uvicorn app.main:app
    2. FastAPI triggers the on_startup event
    3. wait_for_db() polls PostgreSQL with SELECT 1 until it responds
       (PostgreSQL can take a few seconds to be ready inside Docker)
    4. Once the DB is ready, the service begins accepting requests

Why wait_for_db instead of relying on depends_on:
    Docker's depends_on only waits for the container to START, not for
    PostgreSQL inside it to be ready to accept connections. wait_for_db
    adds application-level readiness polling so the service doesn't crash
    on the first request while the DB is still initializing.

Routes registered:
    All routes are prefixed with /api/v1/auth (see app/api/routes.py):
        POST /api/v1/auth/signup
        POST /api/v1/auth/login
        POST /api/v1/auth/refresh
        POST /api/v1/auth/logout

    Utility:
        GET  /          →  liveness check (service is running)
        GET  /health    →  health check (used by docker-compose and monitoring)

Model imports:
    The 'from app.models import ...' lines at the top have no direct usage
    in this file. They exist to ensure SQLAlchemy registers every ORM model
    class in Base.metadata before any query runs. Without these imports,
    foreign key relationships between models would not be resolved.

Dependencies:
    - app.api.routes   →  the router with all auth endpoints
    - app.db.base      →  Base (for model registration)
    - app.db.session   →  engine (for startup DB check)
    - app.models.*     →  imported for side-effect registration with Base
"""

import logging
import time

from fastapi import FastAPI
from sqlalchemy import text

from app.api.routes import router
from app.core.logging import LoggingMiddleware, configure_logging
from app.db.base import Base
from app.db.session import engine

# Import all models so SQLAlchemy registers them in Base.metadata.
# Do not remove these — they are needed for FK resolution even if unused here.
from app.models import user, token, organization, group, user_group, invitation

configure_logging("auth-service")
log = logging.getLogger("auth-service")

app = FastAPI(title="Auth Service")
app.add_middleware(LoggingMiddleware)

app.include_router(router, prefix="/api/v1/auth", tags=["Auth"])


@app.get("/")
def root():
    """Liveness check — confirms the service process is running."""
    return {"message": "Auth Service Running"}


@app.get("/health")
def health():
    """
    Health check endpoint.

    Used by docker-compose healthcheck and future monitoring/load balancers.
    Returns 200 OK as long as the service process is alive.
    Does not check database connectivity (that is handled at startup).
    """
    return {"status": "ok", "service": "auth-service"}


def wait_for_db(connectable, retries: int = 10, delay: int = 2) -> bool:
    """
    Block until the database accepts connections, with retry logic.

    Sends a cheap SELECT 1 to PostgreSQL on each attempt. Logs a warning
    for each failed attempt and raises RuntimeError if all retries are exhausted.

    This is called during the startup event so that the service does not
    begin serving traffic until the database is reachable.

    Args:
        connectable: A SQLAlchemy engine or connection object.
        retries:     Maximum number of connection attempts (default: 10).
        delay:       Seconds to wait between attempts (default: 2).

    Returns:
        True when the database is available.

    Raises:
        RuntimeError: If all retries are exhausted without a successful connection.
    """
    for attempt in range(1, retries + 1):
        try:
            with connectable.connect() as conn:
                conn.execute(text("SELECT 1"))
            log.info("Database is available")
            return True
        except Exception as exc:
            log.warning("DB not ready (attempt %d/%d): %s", attempt, retries, exc)
            time.sleep(delay)
    raise RuntimeError("Database not available after retries")


def run_migrations() -> None:
    """
    Apply all pending Alembic migrations at startup.

    Reads alembic.ini from the service root (/app/alembic.ini inside Docker).
    The alembic/env.py picks up POSTGRES_* env vars to build the DB URL so
    no hardcoded credentials are needed here.

    Safe to run on every startup — migration 0001 uses IF NOT EXISTS so it
    is a no-op if tables already exist (e.g. created by init.sql).
    """
    from alembic.config import Config
    from alembic import command as alembic_command

    alembic_cfg = Config("alembic.ini")
    alembic_command.upgrade(alembic_cfg, "head")
    log.info("Alembic migrations applied successfully")


@app.on_event("startup")
def on_startup():
    """
    Run on service startup before accepting any requests.

    1. Waits for the PostgreSQL database to be ready.
    2. Applies any pending Alembic migrations (idempotent — safe on every restart).

    If the DB is not reachable after all retries, the service exits with a
    RuntimeError, which causes the container to restart (as configured in
    docker-compose).
    """
    wait_for_db(engine, retries=10, delay=2)
    run_migrations()
