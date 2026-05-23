"""
Request ID Middleware (app/core/middleware.py)

Purpose:
    Stamps every incoming request with a UUID before any route handler runs.
    This UUID (request_id) enables distributed tracing — tracking one request
    across multiple services.

How it works:
    Every request goes through RequestIDMiddleware.dispatch() before reaching
    any route handler:
        1. Generates a UUID: "3f2a1b4c-8d2e-4f1a-b3c9-..."
        2. Attaches it to request.state.request_id
        3. Calls call_next(request) — runs the actual route handler
        4. Adds x-request-id header to the response

Why request.state:
    request.state is a scratch pad attached to each request. It travels through
    the entire request lifecycle. Middleware writes to it, route handlers and
    error handlers read from it.

Why add it to the response header:
    The client (Bruno, frontend) sees x-request-id in every response. If
    something fails, share the request_id — it can be grepped across all
    service logs to trace the full journey of that request.

Middleware registration order (important):
    In main.py, RequestIDMiddleware is added AFTER CORSMiddleware.
    FastAPI processes middleware in REVERSE registration order on incoming
    requests — so RequestIDMiddleware runs FIRST, stamping request_id before
    any error handler or CORS logic needs it.
"""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.request_id = str(uuid.uuid4())
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000)
        response.headers["x-request-id"] = request.state.request_id
        logger.info(
            "request",
            extra={
                "request_id": request.state.request_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response
