"""
JWT Validation (app/core/security.py)

Purpose:
    Validates the JWT access token on every protected request.
    Used as a FastAPI Depends() dependency — protected routes inject this
    function and receive the decoded payload if the token is valid.

Validation steps:
    1. Read the Authorization header from the incoming request
    2. Check it starts with "Bearer " → if not → 401 TOKEN_MISSING
    3. Extract the token string (everything after "Bearer ")
    4. Decode the JWT using SECRET_KEY and ALGORITHM
       → If expired   → 401 TOKEN_EXPIRED
       → If invalid   → 401 TOKEN_INVALID
       → If valid     → return the decoded payload dict

Decoded payload (set by auth-service at login):
    {
        "sub":    "alice@acme.com",
        "org_id": "550e8400-e29b-41d4-a716-446655440000",
        "groups": ["admin"],
        "exp":    1748000000
    }

FastAPI Depends pattern:
    @router.get("/api/v1/users")
    async def list_users(payload = Depends(get_token_payload)):
        # Token invalid → HTTPException raised → route never runs → 401 sent
        # Token valid   → payload = { sub, org_id, groups, exp }

Why raise HTTPException instead of return:
    When used as Depends(), raising HTTPException stops execution and sends
    the error to the client. Returning a value would pass it to the route
    handler as the payload argument — which is wrong behavior for an auth guard.

Secret key alignment:
    auth-service signs tokens with SECRET_KEY.
    Gateway verifies with the same SECRET_KEY.
    If they differ, every token is rejected — even valid ones.
    Both read from their own .env files which must have the same value.
"""

from fastapi import Depends, HTTPException, Request
from jose import JWTError, jwt

from app.core.config import settings


def get_token_payload(request: Request) -> dict:
    auth = request.headers.get("Authorization", "")

    if not auth.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail={
                "error_code": "TOKEN_MISSING",
                "message": "Missing or invalid Authorization header",
            },
        )

    token = auth[len("Bearer "):]

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as e:
        if "expired" in str(e).lower():
            raise HTTPException(
                status_code=401,
                detail={
                    "error_code": "TOKEN_EXPIRED",
                    "message": "Access token has expired. Use /api/v1/auth/refresh to get a new one.",
                },
            )
        raise HTTPException(
            status_code=401,
            detail={
                "error_code": "TOKEN_INVALID",
                "message": "Invalid or malformed token",
            },
        )
