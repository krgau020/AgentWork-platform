"""
Gateway Application Bootstrap (app/main.py)

Purpose:
    Creates the FastAPI application, registers middleware and exception handlers,
    configures CORS, and mounts all routes. This is the entry point — uvicorn
    starts here.

Startup sequence:
    1. FastAPI app created
    2. Custom HTTPException handler registered
       → all 401/403/404/503 errors are formatted with:
         { error_code, message, request_id, timestamp }
         matching the standard error shape across all platform services
    3. CORSMiddleware added
       → allows Next.js frontend at localhost:3000 to call the gateway
       → browsers block cross-origin calls by default; this tells them it's OK
    4. RequestIDMiddleware added
       → stamps every request with a UUID for distributed tracing
    5. Router included — all routes from app/api/routes.py become active

Middleware order (important):
    FastAPI processes middleware in REVERSE registration order on incoming requests.
    RequestIDMiddleware is added last → runs FIRST on incoming requests.
    This ensures request_id is always stamped before any error handler reads it.

    Incoming:  RequestIDMiddleware → CORSMiddleware → route handler
    Outgoing:  route handler → CORSMiddleware → RequestIDMiddleware

Custom exception handler:
    get_token_payload() raises HTTPException(401) when a token is bad.
    FastAPI calls http_exception_handler() which injects request_id and
    timestamp — so even auth errors have the full standard error shape.

CORS origins:
    Set to ["http://localhost:3000"] for local development.
    In production, replace with the actual frontend domain.
"""

from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.logging import configure_logging
from app.core.middleware import RequestIDMiddleware

configure_logging("gateway")

app = FastAPI(title="AgentWork Gateway", version="1.0.0")


# ─────────────────────────────────────────────────────────────────────────────
# Custom exception handler
#
# When get_token_payload raises HTTPException, FastAPI calls this handler.
# This formats the error with request_id and timestamp so it matches the
# standard error shape used across all platform services.
# ─────────────────────────────────────────────────────────────────────────────

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
            "request_id": getattr(request.state, "request_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# CORS — allows the frontend (localhost:3000) to call the gateway
#
# Browsers block cross-origin requests by default. Without this middleware,
# any API call from the Next.js frontend would be rejected by the browser
# before it even reaches the gateway.
# ─────────────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
# Request ID middleware — stamps every request with a UUID before routing
# Must be added AFTER CORSMiddleware (middleware runs in reverse add order)
# ─────────────────────────────────────────────────────────────────────────────

app.add_middleware(RequestIDMiddleware)


# ─────────────────────────────────────────────────────────────────────────────
# Router — all routes defined in app/api/routes.py
# ─────────────────────────────────────────────────────────────────────────────

app.include_router(router)
