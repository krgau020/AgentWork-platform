"""
Gateway JWT Validation (app/core/security.py)

Purpose:
    Central authentication layer for the gateway. The verify_jwt_token function
    is injected as a FastAPI dependency (Depends) on every protected route.
    It runs automatically before the route handler is called.

How it works:
    1. Reads the Authorization header from the incoming request.
    2. Splits it into scheme (must be "Bearer") and the raw JWT string.
    3. Decodes and verifies the JWT using JWT_SECRET_KEY and HS256 algorithm.
    4. Returns the decoded payload dict {sub, role, exp} to the route handler.

Error responses:
    No Authorization header   → 401 "Missing authorization token"
    Wrong scheme (not Bearer) → 401 "Invalid auth scheme"
    Token expired             → 401 "Token expired"  (ExpiredSignatureError)
    Invalid/tampered token    → 401 "Invalid token"  (JWTError)

Important:
    ExpiredSignatureError is caught separately from JWTError so the caller
    knows whether to refresh the token or to log in again.
"""

from jose import jwt, JWTError, ExpiredSignatureError
from fastapi import HTTPException, Header
from app.core.config import settings


def verify_jwt_token(authorization: str = Header(None)):
    """
    Validate JWT token from Authorization header.
    """

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization token"
        )

    try:
        scheme, token = authorization.split()

        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=401,
                detail="Invalid auth scheme"
            )

        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=["HS256"]
        )

        return payload

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token expired"
        )

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )