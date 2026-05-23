"""
Structured Logging (app/core/logging.py)

Same JSON format as gateway. Auth-service reads x-request-id from the
incoming request header (forwarded by the gateway on every request) so
its logs share the same request_id — enabling cross-service log correlation.

Public routes (login, signup) also receive x-request-id from Phase 4
gateway update that forwards it on ALL routes, not just protected ones.
"""

import json
import logging
import time
from datetime import datetime, timezone

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

_SERVICE_NAME = "auth-service"

logger = logging.getLogger(__name__)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": _SERVICE_NAME,
            "level": record.levelname,
            "message": record.getMessage(),
        }
        for key in ("request_id", "method", "path", "status", "duration_ms"):
            if hasattr(record, key):
                entry[key] = getattr(record, key)
        return json.dumps(entry)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Logs every request with method, path, status, duration, and request_id."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000)
        logger.info(
            "request",
            extra={
                "request_id": request.headers.get("x-request-id", "-"),
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response


def configure_logging(service_name: str = "auth-service") -> None:
    global _SERVICE_NAME
    _SERVICE_NAME = service_name
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = []
    root.addHandler(handler)
    root.setLevel(logging.INFO)
