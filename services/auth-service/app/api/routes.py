"""
api/routes.py — HTTP route handlers for all auth endpoints.

Role in the system:
    This module is the HTTP boundary of the auth service. It translates
    incoming HTTP requests into calls to auth_service functions, and
    translates the results (or exceptions) back into HTTP responses.

    Routes are intentionally thin — no business logic lives here.
    All decisions (is the password correct? does the token exist?) are
    made in app.services.auth_service. This keeps routes easy to read
    and makes the business logic independently testable.

Error handling strategy:
    All routes use a shared error_response() helper that returns a
    structured JSON body with four fields:
        - error_code:  machine-readable string (e.g. "CONFLICT", "TOKEN_INVALID")
        - message:     human-readable description
        - request_id:  forwarded from the x-request-id header (set by the gateway)
                       for request tracing across services
        - timestamp:   UTC ISO 8601 timestamp for log correlation

Endpoints (all prefixed /api/v1/auth by main.py):
    POST /signup        →  create user + org + default group
    POST /login         →  verify credentials, return token pair
    POST /refresh       →  rotate refresh token, return new token pair
    POST /logout        →  revoke refresh token
    POST /accept-invite →  accept an invitation, create account, return token pair

    /accept-invite is a PUBLIC route (no JWT required). The invitee has no account
    yet, so they cannot authenticate. The gateway forwards this without token validation.
    Security comes from the invite_token being a 256-bit random value stored in the DB.

Dependencies:
    - app.db.session             →  get_db (database session per request)
    - app.schemas.user           →  request/response Pydantic models
    - app.services.auth_service  →  business logic functions
    - Used by: app.main (router is registered there with prefix /api/v1/auth)
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.db.session import get_db
from app.schemas.user import (
    UserCreate, UserLogin, TokenResponse,
    RefreshTokenRequest, LogoutRequest, RefreshResponse,
    AcceptInviteRequest
)
from app.services.auth_service import (
    create_user, login_user, refresh_access_token, logout_user, accept_invite
)

router = APIRouter()


def error_response(status_code: int, error_code: str, message: str, request: Request) -> JSONResponse:
    """
    Build a standardized error JSON response.

    All error responses in the auth service use this format so that clients
    and the gateway can handle errors consistently regardless of which endpoint
    they came from.

    Args:
        status_code: HTTP status code (e.g. 401, 409).
        error_code:  Machine-readable identifier for the error type.
        message:     Human-readable description shown to the client.
        request:     The incoming FastAPI request (used to extract request_id).

    Returns:
        JSONResponse with the structured error body and the given status code.
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "error_code": error_code,
            "message": message,
            "request_id": request.headers.get("x-request-id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


@router.post("/signup")
def signup(user: UserCreate, request: Request, db: Session = Depends(get_db)):
    """
    Register a new user and create their organization.

    Creates four records atomically: organization, user, admin group,
    and user-group membership. If any step fails, nothing is saved.

    Returns:
        200 with {"message": "User created successfully"} on success.
        409 CONFLICT if the email or organization slug is already taken,
            or if the password does not meet policy requirements.
    """
    try:
        create_user(db, user.email, user.password, user.org_name)
        return {"message": "User created successfully"}
    except ValueError as e:
        return error_response(409, "CONFLICT", str(e), request)


@router.post("/login", response_model=TokenResponse)
def login(user: UserLogin, request: Request, db: Session = Depends(get_db)):
    """
    Authenticate a user and issue a JWT token pair.

    Returns a generic "invalid credentials" message for both wrong email and
    wrong password — this prevents user enumeration (an attacker cannot tell
    whether the email exists).

    Returns:
        200 with {access_token, refresh_token} on success.
        401 TOKEN_INVALID if credentials are wrong or account is inactive.
    """
    tokens = login_user(db, user.email, user.password)

    if not tokens:
        return error_response(401, "TOKEN_INVALID", "Invalid email or password", request)

    return {"access_token": tokens[0], "refresh_token": tokens[1]}


@router.post("/refresh", response_model=RefreshResponse)
def refresh(req: RefreshTokenRequest, request: Request, db: Session = Depends(get_db)):
    """
    Rotate a refresh token and issue a new token pair.

    The submitted refresh token is immediately invalidated on success.
    The client must use the new refresh token for subsequent calls.
    Submitting the same refresh token twice will fail on the second attempt.

    Returns:
        200 with {access_token, refresh_token} on success.
        401 TOKEN_INVALID if the token is expired, revoked, or malformed.
    """
    try:
        new_access, new_refresh = refresh_access_token(db, req.refresh_token)
        return {"access_token": new_access, "refresh_token": new_refresh}
    except ValueError:
        return error_response(401, "TOKEN_INVALID", "Invalid or expired refresh token", request)


@router.post("/logout")
def logout(req: LogoutRequest, request: Request, db: Session = Depends(get_db)):
    """
    Revoke a refresh token.

    After this call, the refresh token cannot be used to obtain new access
    tokens. Any existing access tokens remain valid until they expire naturally
    (access tokens are stateless and cannot be individually revoked).

    Returns:
        200 with {"message": "Logged out successfully"} on success.
        401 TOKEN_INVALID if the token is not found or already revoked.
    """
    try:
        logout_user(db, req.refresh_token)
        return {"message": "Logged out successfully"}
    except ValueError:
        return error_response(401, "TOKEN_INVALID", "Token not found or already revoked", request)


@router.post("/accept-invite", response_model=TokenResponse)
def accept_invite_route(req: AcceptInviteRequest, request: Request, db: Session = Depends(get_db)):
    """
    Accept an invitation and create a new user account.

    PUBLIC endpoint — no JWT required. The invitee has no account yet so they
    cannot authenticate. Security is provided by the invite_token itself
    (256-bit random value, one-time use, expires in 7 days).

    On success, the invitation row is deleted and the new user is returned a
    token pair so they are immediately logged in without a separate /login call.

    Returns:
        200 with {access_token, refresh_token} on success.
        400 INVITE_ERROR if the token is invalid, expired, or the email already exists.
    """
    try:
        access_token, refresh_token = accept_invite(db, req.invite_token, req.password)
        return {"access_token": access_token, "refresh_token": refresh_token}
    except ValueError as e:
        return error_response(400, "INVITE_ERROR", str(e), request)
