"""
Gateway Route Handlers (app/api/routes.py)

Purpose:
    All API route definitions for the gateway. Routes either answer directly
    (health check) or forward the request to a downstream service using httpx.

Route categories:

    Public routes — no JWT required, forwarded to auth-service:
        POST /api/v1/auth/signup        → auth-service /api/v1/auth/signup
        POST /api/v1/auth/login         → auth-service /api/v1/auth/login
        POST /api/v1/auth/refresh       → auth-service /api/v1/auth/refresh
        POST /api/v1/auth/logout        → auth-service /api/v1/auth/logout
        POST /api/v1/auth/accept-invite → auth-service /api/v1/auth/accept-invite
        GET  /health                    → gateway responds directly

    /accept-invite is public because the invitee has no account yet and cannot
    present a JWT. Security comes from the invite_token being a 256-bit random
    value (secrets.token_urlsafe(32)) stored in the DB with a 7-day expiry.
    FastAPI route ordering matters: /accept-invite must be registered BEFORE the
    generic /api/v1/auth/{path:path} catch-all (if one existed) so it matches first.

    Protected routes — JWT required, forwarded to user-service:
        /api/v1/orgs/*     → user-service (after token validation + headers)
        /api/v1/users/*    → user-service
        /api/v1/groups/*   → user-service
        /api/v1/policies/* → user-service

Helper functions:
    _error()            — builds standard error JSON with error_code, message,
                          request_id, timestamp. Used for gateway-level errors
                          (503, 504).
    _forward()          — sends the request to a downstream URL using httpx.
                          Passes through body and query params. Returns the
                          downstream response to the client. Handles 503/504.
    _identity_headers() — builds the 4 trusted headers added to every protected
                          forward so downstream services know who the user is.

Identity propagation:
    After JWT validation, gateway extracts identity from the payload and adds:
        x-user-email:  alice@acme.com
        x-org-id:      550e8400-e29b-41d4-a716-446655440000
        x-user-groups: admin
        x-request-id:  3f2a1b4c-8d2e-...
    Downstream services read these headers — they never see the raw JWT.

Path forwarding for user-service:
    request.url.path gives the full path the client sent (/api/v1/users,
    /api/v1/groups, etc.) which matches exactly what user-service expects.
    Appending it to USER_SERVICE_URL requires no path rewriting.

api_route() with multiple methods:
    router.api_route("/api/v1/users", methods=["GET", "POST"]) registers
    one function for multiple HTTP methods — cleaner than stacking decorators.

{path:path} parameter:
    Matches any path including slashes. /api/v1/users/{path:path} matches:
        /api/v1/users/some-id
        /api/v1/users/some-id/groups
        /api/v1/users/some-id/groups/group-id
"""

from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.security import get_token_payload

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _error(status: int, code: str, message: str, request: Request) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={
            "error_code": code,
            "message": message,
            "request_id": getattr(request.state, "request_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


async def _forward(request: Request, url: str, extra_headers: dict = None) -> JSONResponse:
    body = await request.body()

    if request.query_params:
        url = f"{url}?{request.query_params}"

    headers = {"Content-Type": "application/json"}
    if extra_headers:
        headers.update(extra_headers)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.request(
                method=request.method,
                url=url,
                content=body,
                headers=headers,
            )
        try:
            content = resp.json()
        except Exception:
            content = {"message": resp.text}
        return JSONResponse(status_code=resp.status_code, content=content)

    except httpx.ConnectError:
        return _error(503, "SERVICE_UNAVAILABLE", "Downstream service is unreachable", request)
    except httpx.TimeoutException:
        return _error(504, "GATEWAY_TIMEOUT", "Downstream service did not respond in time", request)


def _identity_headers(payload: dict, request: Request) -> dict:
    return {
        "x-user-email": payload.get("sub", ""),
        "x-org-id": str(payload.get("org_id", "")),
        "x-user-groups": ",".join(payload.get("groups", [])),
        "x-request-id": getattr(request.state, "request_id", ""),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Health check — gateway answers directly, no forwarding
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/health")
def health():
    return {"status": "ok", "service": "gateway"}


# ─────────────────────────────────────────────────────────────────────────────
# Auth routes — PUBLIC, no JWT required
# Forwarded directly to auth-service
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/api/v1/auth/signup")
async def signup(request: Request):
    return await _forward(request, f"{settings.AUTH_SERVICE_URL}/api/v1/auth/signup")


@router.post("/api/v1/auth/login")
async def login(request: Request):
    return await _forward(request, f"{settings.AUTH_SERVICE_URL}/api/v1/auth/login")


@router.post("/api/v1/auth/refresh")
async def refresh(request: Request):
    return await _forward(request, f"{settings.AUTH_SERVICE_URL}/api/v1/auth/refresh")


@router.post("/api/v1/auth/logout")
async def logout(request: Request):
    return await _forward(request, f"{settings.AUTH_SERVICE_URL}/api/v1/auth/logout")


@router.post("/api/v1/auth/accept-invite")
async def accept_invite(request: Request):
    return await _forward(request, f"{settings.AUTH_SERVICE_URL}/api/v1/auth/accept-invite")


# ─────────────────────────────────────────────────────────────────────────────
# User-service routes — PROTECTED, JWT required
#
# Gateway validates the token, extracts identity, adds identity headers,
# then forwards to user-service. User-service never sees the raw JWT.
#
# request.url.path gives the full path (/api/v1/users, /api/v1/groups, etc.)
# which matches exactly what user-service expects — so we append it directly.
# ─────────────────────────────────────────────────────────────────────────────

# ── Organizations ────────────────────────────────────────────────────────────

@router.api_route("/api/v1/orgs", methods=["GET", "POST"])
async def orgs(request: Request, payload: dict = Depends(get_token_payload)):
    return await _forward(request, settings.USER_SERVICE_URL + request.url.path, _identity_headers(payload, request))


@router.api_route("/api/v1/orgs/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def orgs_detail(path: str, request: Request, payload: dict = Depends(get_token_payload)):
    return await _forward(request, settings.USER_SERVICE_URL + request.url.path, _identity_headers(payload, request))


# ── Users ────────────────────────────────────────────────────────────────────

@router.api_route("/api/v1/users", methods=["GET", "POST"])
async def users(request: Request, payload: dict = Depends(get_token_payload)):
    return await _forward(request, settings.USER_SERVICE_URL + request.url.path, _identity_headers(payload, request))


@router.api_route("/api/v1/users/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def users_detail(path: str, request: Request, payload: dict = Depends(get_token_payload)):
    return await _forward(request, settings.USER_SERVICE_URL + request.url.path, _identity_headers(payload, request))


# ── Groups ───────────────────────────────────────────────────────────────────

@router.api_route("/api/v1/groups", methods=["GET", "POST"])
async def groups(request: Request, payload: dict = Depends(get_token_payload)):
    return await _forward(request, settings.USER_SERVICE_URL + request.url.path, _identity_headers(payload, request))


@router.api_route("/api/v1/groups/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def groups_detail(path: str, request: Request, payload: dict = Depends(get_token_payload)):
    return await _forward(request, settings.USER_SERVICE_URL + request.url.path, _identity_headers(payload, request))


# ── Policies ─────────────────────────────────────────────────────────────────

@router.api_route("/api/v1/policies", methods=["GET", "POST"])
async def policies(request: Request, payload: dict = Depends(get_token_payload)):
    return await _forward(request, settings.USER_SERVICE_URL + request.url.path, _identity_headers(payload, request))


@router.api_route("/api/v1/policies/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def policies_detail(path: str, request: Request, payload: dict = Depends(get_token_payload)):
    return await _forward(request, settings.USER_SERVICE_URL + request.url.path, _identity_headers(payload, request))
