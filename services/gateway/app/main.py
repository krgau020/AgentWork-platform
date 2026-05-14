"""
FinSight API Gateway — Application Bootstrap (main.py)

Purpose:
    This is the entry point for the gateway service. It initializes the FastAPI
    application, registers all middleware, configures CORS, and mounts the router.

What this file does:
    1. Creates the FastAPI app instance.
    2. Registers add_request_context middleware — stamps every request with a
       unique UUID (request_id) for distributed tracing.
    3. Adds CORSMiddleware — allows browser-based frontends to call this API
       across different ports/domains.
    4. Includes the router from app.api.routes — all route handlers live there.

Middleware order matters:
    Middleware runs top-to-bottom on request, bottom-to-top on response.
    add_request_context wraps every request before any route handler runs.

How to run locally (outside Docker):
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

Port: 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.middleware import add_request_context

app = FastAPI(title="FinSight Gateway")


# =========================
# Middleware Registration
# =========================

app.middleware("http")(add_request_context)


# =========================
# CORS Configuration
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# Routes
# =========================

app.include_router(router)