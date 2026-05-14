"""
Auth Service — Business Logic (app/services/auth_service.py)

Purpose:
    Contains all authentication business logic. No HTTP concerns here —
    this layer only deals with data, DB operations, and token management.
    Routes call these functions and map errors to HTTP responses.

Functions:
    create_user(db, email, password)
        Checks email uniqueness, validates password policy (via hash_password),
        hashes the password with Argon2, saves user to DB. Raises ValueError
        if user already exists or password is too weak.

    login_user(db, email, password)
        Finds user by email, verifies password against Argon2 hash.
        On success: creates access_token {sub, role, exp} and refresh_token {sub, exp},
        saves refresh_token to tokens table, returns both tokens.
        Returns None on failure (route maps to 401).

    refresh_access_token(db, refresh_token)
        Validates refresh_token exists in DB (if not, it was revoked or never existed).
        Decodes token to get email, fetches user from DB to get current role.
        Creates and returns a new access_token with fresh role from DB.
        Role is fetched fresh so changes to a user's role are reflected immediately.
        Raises ValueError on any failure (route maps to 401).
"""

from sqlalchemy.orm import Session
from app.models.user import User
from app.models.token import Token
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)


def create_user(db: Session, email: str, password: str):
    if db.query(User).filter(User.email == email).first():
        raise ValueError("User already exists")

    user = User(email=email, password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(password, user.password):
        return None

    access_token = create_access_token({"sub": user.email, "role": user.role})
    refresh_token = create_refresh_token({"sub": user.email})

    # Store refresh token (for revocation)
    db_token = Token(user_id=user.id, refresh_token=refresh_token)
    db.add(db_token)
    db.commit()

    return access_token, refresh_token


def refresh_access_token(db: Session, refresh_token: str):
    token_entry = db.query(Token).filter(Token.refresh_token == refresh_token).first()

    if not token_entry:
        raise ValueError("Invalid refresh token")

    payload = decode_token(refresh_token)
    email = payload.get("sub")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise ValueError("User not found")

    return create_access_token({"sub": user.email, "role": user.role})
