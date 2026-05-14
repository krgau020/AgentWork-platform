"""
Gateway Route Handlers (app/api/routes.py)

Purpose:
    Defines all API endpoints exposed by the gateway. Each route either returns
    a direct response or forwards the request to a downstream service via httpx.

Route categories:
    Public routes (no JWT required):
        POST /auth/login    → forwards to auth-service (returns tokens)
        POST /auth/signup   → forwards to auth-service (creates user)
        POST /auth/refresh  → forwards to auth-service (returns new access_token)
        GET  /health        → gateway responds directly (liveness check)

    Protected routes (JWT validation required via Depends):
        GET /documents      → validates token, then forwards to document-service
                              with identity headers (x-user-email, x-user-role)

Identity propagation on protected routes:
    Gateway extracts email and role from the validated token and forwards them
    as internal headers. Downstream services read these instead of the raw JWT.

Error handling:
    httpx.ConnectError → 503 Service Unavailable (downstream service is down)
    JWT errors         → 401 (handled by verify_jwt_token in core/security.py)
"""

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
from app.core.security import verify_jwt_token
from app.core.config import settings
import httpx

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "Gateway running"}


# =========================
# AUTH ROUTES
# =========================

@router.post("/auth/login")
async def login(request: Request):
    body = await request.json()

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.AUTH_SERVICE_URL}/auth/login",
                json=body
            )
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Auth service unavailable")

    return JSONResponse(status_code=response.status_code, content=response.json())


@router.post("/auth/signup")
async def signup(request: Request):
    body = await request.json()

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.AUTH_SERVICE_URL}/auth/signup",
                json=body
            )
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Auth service unavailable")

    return JSONResponse(status_code=response.status_code, content=response.json())


@router.post("/auth/refresh")
async def refresh_token(request: Request):
    body = await request.json()

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.AUTH_SERVICE_URL}/auth/refresh",
                json=body
            )
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Auth service unavailable")

    return JSONResponse(status_code=response.status_code, content=response.json())


# =========================
# DOCUMENT ROUTES
# =========================

@router.get("/documents")
async def documents(
    request: Request,
    user=Depends(verify_jwt_token)
):
    headers = {
        "x-user-email": user["sub"],
        "x-user-role": user.get("role", "user"),
        "x-request-id": request.state.request_id
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://document-service:8002/documents",
                headers=headers
            )
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Document service unavailable")

    return JSONResponse(status_code=response.status_code, content=response.json())
