"""
Handles password hashing and JWT token creation/validation.
"""

from passlib.context import CryptContext
import re
from jose import jwt
from datetime import datetime, timedelta
from app.core.config import settings

# Use Argon2 for new hashes, keep bcrypt for legacy verification
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

# Password policy (real-world):
# - At least 12 characters
# - At least one uppercase, one lowercase, one digit, one special char
def validate_password_policy(password: str):
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter.")
    if not re.search(r"[0-9]", password):
        raise ValueError("Password must contain at least one digit.")
    if not re.search(r"[^A-Za-z0-9]", password):
        raise ValueError("Password must contain at least one special character.")
    if len(password) > 256:
        raise ValueError("Password must be less than 256 characters.")


def hash_password(password: str):
    validate_password_policy(password)
    return pwd_context.hash(password)


def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict):
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    return jwt.encode(
        {"sub": data["sub"], "exp": expire},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )


def decode_token(token: str):
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])