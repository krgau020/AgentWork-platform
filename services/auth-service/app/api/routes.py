"""
Auth Service — API Route Handlers (app/api/routes.py)

Purpose:
    Defines all HTTP endpoints for authentication. Each route validates the
    incoming request, calls the appropriate business logic from auth_service.py,
    and handles errors with proper HTTP status codes.

Routes:
    POST /auth/signup   → creates a new user account.
                          Raises 400 if email already exists or password is too weak.
    POST /auth/login    → verifies credentials, returns access + refresh tokens.
                          Raises 401 if credentials are wrong.
    POST /auth/refresh  → validates refresh_token, returns a new access_token.
                          Raises 401 if refresh token is invalid or revoked.

Design notes:
    - get_db() is a FastAPI dependency that provides a DB session per request
      and guarantees the session is closed after the request, even on errors.
    - Business logic lives in app/services/auth_service.py, not here.
      Routes only handle HTTP concerns (request parsing, error mapping).
    - ValueError from service layer maps to HTTP 400 or 401 as appropriate.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.schemas.user import UserCreate, UserLogin, TokenResponse, RefreshTokenRequest
from app.services.auth_service import create_user, login_user, refresh_access_token

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    try:
        return create_user(db, user.email, user.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenResponse)
def login(user: UserLogin, db: Session = Depends(get_db)):
    tokens = login_user(db, user.email, user.password)

    if not tokens:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"access_token": tokens[0], "refresh_token": tokens[1]}


@router.post("/refresh")
def refresh(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    try:
        new_token = refresh_access_token(db, request.refresh_token)
        return {"access_token": new_token}
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token")