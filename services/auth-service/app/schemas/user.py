"""
schemas/user.py — Pydantic request and response schemas for auth endpoints.

Role in the system:
    Schemas define the shape of data coming IN (request bodies) and going OUT
    (response bodies) through the API. They are separate from ORM models
    intentionally: ORM models represent database rows; schemas represent what
    the HTTP API accepts and returns.

    FastAPI uses these schemas to:
        1. Automatically parse and validate incoming JSON request bodies.
        2. Generate the OpenAPI documentation at /docs.
        3. Serialize response data (when used as response_model).

    Using EmailStr (instead of plain str) for email fields means FastAPI will
    reject requests with invalid email formats before they reach any service
    logic — the client gets a clear 422 Unprocessable Entity with a field-level
    error message.

Schema map:
    UserCreate          →  POST /signup body
    UserLogin           →  POST /login body
    TokenResponse       →  POST /login response
    RefreshTokenRequest →  POST /refresh body
    RefreshResponse     →  POST /refresh response
    LogoutRequest       →  POST /logout body

Dependencies:
    - pydantic.BaseModel   →  base class for all schemas
    - pydantic.EmailStr    →  validated email field (requires email-validator package)
    - Used by: app.api.routes
"""

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """
    Body for POST /signup.

    Creates a new user, organization, and default admin group in one transaction.

    Fields:
        email:    Must be a valid email format. Globally unique across the platform.
        password: Must satisfy the password policy (min 8 chars, upper, lower,
                  digit, special character). Hashed before storage — never logged.
        org_name: The display name of the organization being created (e.g. "Acme Corp").
                  A URL-safe slug is derived from this automatically.
    """
    email:    EmailStr
    password: str
    org_name: str


class UserLogin(BaseModel):
    """
    Body for POST /login.

    Fields:
        email:    The user's registered email address.
        password: Plain-text password — compared against the stored hash.
    """
    email:    EmailStr
    password: str


class TokenResponse(BaseModel):
    """
    Response for POST /login.

    Fields:
        access_token:  Short-lived JWT (default 120 min). Send this in the
                       Authorization header: "Bearer <access_token>".
                       Contains: sub, org_id, groups, exp.
        refresh_token: Long-lived JWT (default 7 days). Use this only to
                       call POST /refresh. Do not send it on regular API calls.
    """
    access_token:  str
    refresh_token: str


class RefreshTokenRequest(BaseModel):
    """
    Body for POST /refresh.

    Fields:
        refresh_token: The refresh token received from /login or the previous /refresh.
    """
    refresh_token: str


class RefreshResponse(BaseModel):
    """
    Response for POST /refresh.

    Returns a brand new token pair. The submitted refresh_token is immediately
    invalidated (token rotation) — store the new one and discard the old.

    Fields:
        access_token:  New short-lived JWT.
        refresh_token: New long-lived JWT (old one is now revoked).
    """
    access_token:  str
    refresh_token: str


class LogoutRequest(BaseModel):
    """
    Body for POST /logout.

    Fields:
        refresh_token: The refresh token to revoke. After this call, the
                       token cannot be used to obtain new access tokens.
    """
    refresh_token: str
