"""
Auth Service — Security Utilities (app/core/security.py)

Purpose:
    All cryptographic operations for the auth service live here.
    Covers password hashing, password policy validation, and JWT operations.

Password hashing:
    Uses Argon2 as the primary algorithm (winner of Password Hashing Competition).
    bcrypt is kept as a fallback to verify old hashes during migration.
    passlib's CryptContext handles algorithm selection automatically.
    Hashing is one-way — stored hashes cannot be reversed to get the original password.

Password policy (validate_password_policy):
    Enforced at signup. Raises ValueError if any rule is violated.
    Rules: min 8 chars, max 256 chars, at least one uppercase, lowercase, digit,
    and special character. ValueError is caught in routes.py and returned as HTTP 400.

JWT functions:
    create_access_token  — signs payload {sub, role, exp} with SECRET_KEY using HS256.
                           exp = now + ACCESS_TOKEN_EXPIRE_MINUTES.
    create_refresh_token — signs payload {sub, exp} only (no role).
                           exp = now + REFRESH_TOKEN_EXPIRE_DAYS.
    decode_token         — decodes and verifies a JWT. Raises JWTError if invalid.

Algorithm:
    HS256 = HMAC + SHA-256. Symmetric — same SECRET_KEY signs and verifies.
    Only this service and the gateway need the key.
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