"""
core/security.py — Password hashing and JWT token management.

Role in the system:
    This is the cryptographic foundation of the auth service. Every password
    stored in the database and every token issued to a client passes through
    this module. No other module should handle raw passwords or token strings
    directly — all crypto lives here.

Design decisions:
    - Argon2 is used as the primary hashing algorithm. It won the 2015 Password
      Hashing Competition and is memory-hard, making it resistant to GPU and
      ASIC brute-force attacks. bcrypt is retained as a fallback so that any
      passwords hashed with bcrypt before this change continue to work — passlib
      handles the algorithm negotiation automatically on verify.

    - JWTs are signed with HS256 (HMAC-SHA256) using a shared SECRET_KEY.
      All services that need to verify tokens must share this key. If the
      platform later moves to a public-key model (RS256), only this file and
      config.py need to change.

    - Access tokens are short-lived (default 120 min) to limit the damage
      window if a token is stolen. Refresh tokens are long-lived (7 days) and
      stored in the database so they can be explicitly revoked on logout.

    - decode_token wraps JWTError in a ValueError so callers don't need to
      know about the jose library. Routes catch ValueError and return 401.

Password policy enforced on every hash:
    - Minimum 8 characters (prevents trivially weak passwords)
    - At least one uppercase, lowercase, digit, and special character
    - Maximum 256 characters (prevents hash-flooding: hashing a 1 MB string
      is expensive server-side; bounding the input protects against DoS)

Dependencies:
    - app.core.config.settings  →  SECRET_KEY, ALGORITHM, expiry values
    - Used by: app.services.auth_service (hash_password, verify_password,
      create_access_token, create_refresh_token, decode_token)
"""

from passlib.context import CryptContext
from jose import jwt, JWTError
import re
from datetime import datetime, timedelta
from app.core.config import settings

# Argon2 primary, bcrypt fallback for any pre-existing hashes
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")


def validate_password_policy(password: str):
    """
    Enforce the platform password policy before hashing.

    Raises ValueError with a human-readable message if the password
    violates any rule. Called inside hash_password so the policy is
    always enforced at write time, never bypassed.

    Args:
        password: The plain-text password supplied by the user.

    Raises:
        ValueError: Describes exactly which rule was violated.
    """
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


def hash_password(password: str) -> str:
    """
    Validate and hash a plain-text password using Argon2.

    Always call this before storing a password. Never store plain text.

    Args:
        password: The plain-text password to hash.

    Returns:
        Argon2 hash string safe to store in the database.

    Raises:
        ValueError: If the password violates the password policy.
    """
    validate_password_policy(password)
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a plain-text password against a stored hash.

    Handles both Argon2 and bcrypt hashes transparently. If a bcrypt
    hash is verified successfully, passlib can optionally re-hash it
    to Argon2 on the fly (rehash-on-login pattern, not wired here yet).

    Args:
        plain:   The plain-text password from the login request.
        hashed:  The hash stored in the database.

    Returns:
        True if the password matches, False otherwise.
    """
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    """
    Issue a short-lived JWT access token.

    The payload should include at minimum:
        - "sub": user email (subject)
        - "org_id": organization UUID string
        - "groups": list of group names the user belongs to

    The gateway reads org_id and groups from this token for
    authorization decisions without hitting the database.

    Args:
        data: Dict of claims to embed. "exp" is added automatically.

    Returns:
        Signed JWT string to return to the client.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """
    Issue a long-lived JWT refresh token.

    Refresh tokens intentionally carry only "sub" (email) and "exp".
    They have no authorization claims because they are not used for
    resource access — only to obtain a new access token. Keeping them
    minimal limits the damage if one is intercepted.

    The token string is also stored in the tokens table so it can be
    revoked explicitly on logout.

    Args:
        data: Must contain "sub" key with the user's email.

    Returns:
        Signed JWT string to store and return to the client.
    """
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return jwt.encode(
        {"sub": data["sub"], "exp": expire},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.

    Verifies the signature and expiry. Raises ValueError (not JWTError)
    so that callers (routes) can catch a single exception type without
    depending on the jose library directly.

    Args:
        token: The JWT string from the client request.

    Returns:
        The decoded payload dict (e.g. {"sub": ..., "org_id": ..., "groups": ...}).

    Raises:
        ValueError: If the token is expired, malformed, or has an invalid signature.
    """
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise ValueError("Invalid or expired token")
