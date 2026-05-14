"""
Auth Service — Application Bootstrap (main.py)

Purpose:
    Entry point for the auth service. Initializes FastAPI, registers all routes
    under the /auth prefix, and handles database startup.

What this file does:
    1. Creates the FastAPI app instance.
    2. Mounts the router from app.api.routes with prefix /auth.
       All endpoints are accessible at /auth/signup, /auth/login, /auth/refresh.
    3. On startup: waits for PostgreSQL to be ready (with retry logic),
       then auto-creates all DB tables via SQLAlchemy metadata.

Startup behavior (on_startup):
    wait_for_db() retries up to 10 times (2s apart) before failing.
    This handles the race condition where auth-service starts before postgres
    is fully ready inside Docker Compose.
    Base.metadata.create_all() creates users and tokens tables if they don't exist.
    In production: replace create_all with Alembic migrations.

How to run locally (outside Docker):
    uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

Port: 8001
"""

from fastapi import FastAPI
import time
import logging
from sqlalchemy import text
from app.api.routes import router
from app.db.base import Base
from app.db.session import engine
from app.models import user, token

log = logging.getLogger("auth-service")

app = FastAPI(title="Auth Service")

app.include_router(router, prefix="/auth", tags=["Auth"])


@app.get("/")
def root():
	return {"message": "Auth Service Running"}


def wait_for_db(connectable, retries=10, delay=2):
	"""Wait for the database to be available, with retries."""
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


@app.on_event("startup")
def on_startup():
	# Wait for DB then create tables. In production prefer migrations (alembic).
	wait_for_db(engine, retries=10, delay=2)
	Base.metadata.create_all(bind=engine)