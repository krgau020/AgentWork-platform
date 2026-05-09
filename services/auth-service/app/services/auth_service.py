"""
Business logic for authentication.
Handles signup, login, token creation, and revocation.
"""

from sqlalchemy.orm import Session
from app.models.user import User
from app.models.token import Token
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token
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




from app.core.security import decode_token

def refresh_access_token(db, refresh_token: str):
    token_entry = db.query(Token).filter(Token.refresh_token == refresh_token).first()

    if not token_entry:
        raise ValueError("Invalid refresh token")

    payload = decode_token(refresh_token)

    return create_access_token({
        "sub": payload["sub"]
    })