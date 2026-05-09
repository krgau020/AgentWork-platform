"""
Defines API endpoints for authentication.
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