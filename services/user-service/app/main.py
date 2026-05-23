"""
User-Service Bootstrap (app/main.py)

Same pattern as auth-service — wait for DB on startup, standard error format,
include all routes.

One difference: no JWT logic anywhere in this service.
The gateway already validated the token before this service sees any request.
"""

import logging
import time
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.routes import router
from app.core.logging import LoggingMiddleware, configure_logging
from app.db.session import engine

configure_logging("user-service")
log = logging.getLogger("user-service")

app = FastAPI(title="AgentWork User Service", version="1.0.0")
app.add_middleware(LoggingMiddleware)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, dict) else {
        "error_code": "ERROR",
        "message": str(exc.detail),
    }
    return JSONResponse(
        status_code=exc.status_code,
        content={
            **detail,
            "request_id": request.headers.get("x-request-id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


def wait_for_db(retries: int = 10, delay: int = 2):
    for attempt in range(1, retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            log.info("Database is available")
            return
        except Exception as exc:
            log.warning("DB not ready (attempt %d/%d): %s", attempt, retries, exc)
            time.sleep(delay)
    raise RuntimeError("Database did not become available")


@app.on_event("startup")
def startup():
    wait_for_db()


@app.get("/health")
def health():
    return {"status": "ok", "service": "user-service"}


app.include_router(router)
