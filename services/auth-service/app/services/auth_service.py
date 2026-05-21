"""
services/auth_service.py — Core authentication business logic.

Role in the system:
    This module contains all the stateful auth operations: creating users,
    verifying credentials, issuing tokens, rotating refresh tokens, and
    revoking sessions. Routes in api/routes.py are thin wrappers that call
    these functions and translate results into HTTP responses.

    Keeping business logic here (and not in routes) means it can be tested
    independently of HTTP and reused if the transport layer ever changes.

Signup flow (create_user):
    1. Validate email uniqueness
    2. Derive a URL-safe slug from org_name, validate slug uniqueness
    3. Create Organization row
    4. Create User row with hashed password and org_id
    5. Create default "admin" Group for the org
    6. Add the user to the admin Group (UserGroup join row)
    7. All 4 inserts are committed in a single transaction — if any step
       fails, nothing is saved (atomicity guaranteed by db.flush + db.commit).

Login flow (login_user):
    1. Look up user by email, verify password hash
    2. Check is_active (blocked users cannot log in)
    3. Query the user's current groups from user_groups + groups tables
    4. Build JWT payload: sub (email), org_id, groups list
    5. Issue access token (short-lived, stateless) and refresh token
    6. Store refresh token in tokens table (for future revocation)

Refresh flow (refresh_access_token):
    1. Look up the refresh token in the tokens table (verifies it hasn't been revoked)
    2. Decode and validate the JWT (verifies it hasn't expired)
    3. Delete the old token row immediately (rotation — one-time use)
    4. Re-query the user's groups (picks up any membership changes since last login)
    5. Issue new access token + refresh token, store new refresh token row

Logout flow (logout_user):
    1. Find the refresh token row in the tokens table
    2. Delete it — token is now revoked, cannot be used again

Design decisions:
    - db.flush() is used between inserts in create_user so each row gets its
      DB-assigned UUID before the next row references it as a FK — but no
      data is committed to disk until db.commit() at the end.
    - Groups are re-fetched from the DB on every login and refresh, not cached
      in the token. This means group changes take effect at the next token
      rotation without requiring a logout.
    - Email is used as the JWT subject ("sub") rather than user ID. This is
      readable for debugging. If email ever becomes mutable, switch sub to user ID.

Dependencies:
    - app.models.*          →  ORM models (User, Token, Organization, Group, UserGroup)
    - app.core.security     →  hash_password, verify_password, create_*_token, decode_token
    - Used by: app.api.routes
"""

import re
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.token import Token
from app.models.organization import Organization
from app.models.group import Group
from app.models.user_group import UserGroup
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)


def _slugify(name: str) -> str:
    """
    Convert an organization name to a URL-safe slug.

    Lowercases, replaces any non-alphanumeric sequences with a hyphen,
    and strips leading/trailing hyphens.

    Example:
        "Acme Corp!"  →  "acme-corp"
        "  My Company 2024  "  →  "my-company-2024"
    """
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


def _get_user_groups(db: Session, user_id) -> list[str]:
    """
    Return the list of group names the user currently belongs to.

    Performs an inner join: user_groups → groups, filtered by user_id.
    Called at login and refresh so the JWT always reflects current membership.

    Args:
        db:      Active database session.
        user_id: UUID of the user to query.

    Returns:
        List of group name strings (e.g. ["admin", "billing"]).
        Empty list if the user has no group assignments.
    """
    rows = (
        db.query(Group.name)
        .join(UserGroup, Group.id == UserGroup.group_id)
        .filter(UserGroup.user_id == user_id)
        .all()
    )
    return [r.name for r in rows]


def create_user(db: Session, email: str, password: str, org_name: str):
    """
    Register a new user and bootstrap their organization.

    Creates four rows in a single atomic transaction:
        organizations → users → groups → user_groups

    If any step fails (e.g. duplicate email or slug), no rows are committed.

    Args:
        db:       Active database session.
        email:    User's email address. Must be globally unique.
        password: Plain-text password. Will be validated and hashed.
        org_name: Display name for the new organization.

    Returns:
        The newly created User ORM object (with org_id populated).

    Raises:
        ValueError: If the email is already registered.
        ValueError: If the organization slug (derived from org_name) is already taken.
        ValueError: If the password violates the password policy.
    """
    if db.query(User).filter(User.email == email).first():
        raise ValueError("User already exists")

    slug = _slugify(org_name)
    if db.query(Organization).filter(Organization.slug == slug).first():
        raise ValueError("Organization name already taken")

    org = Organization(name=org_name, slug=slug)
    db.add(org)
    db.flush()  # assigns org.id without committing

    user = User(email=email, password=hash_password(password), org_id=org.id)
    db.add(user)
    db.flush()  # assigns user.id

    group = Group(org_id=org.id, name="admin", description="Default admin group")
    db.add(group)
    db.flush()  # assigns group.id

    db.add(UserGroup(user_id=user.id, group_id=group.id))
    db.commit()
    db.refresh(user)
    return user


def login_user(db: Session, email: str, password: str):
    """
    Authenticate a user and issue a token pair.

    Returns None instead of raising on bad credentials intentionally:
    the route converts None → 401 error response without exposing whether
    the email exists (prevents user enumeration).

    Args:
        db:       Active database session.
        email:    Email from the login request.
        password: Plain-text password from the login request.

    Returns:
        Tuple (access_token, refresh_token) on success.
        None if credentials are invalid or the account is inactive.
    """
    user = db.query(User).filter(User.email == email).first()

    if not user or not user.is_active or not verify_password(password, user.password):
        return None

    groups = _get_user_groups(db, user.id)
    payload = {
        "sub":    user.email,
        "org_id": str(user.org_id) if user.org_id else None,
        "groups": groups,
    }

    access_token = create_access_token(payload)
    refresh_token = create_refresh_token({"sub": user.email})

    db.add(Token(user_id=user.id, refresh_token=refresh_token))
    db.commit()

    return access_token, refresh_token


def refresh_access_token(db: Session, refresh_token: str):
    """
    Rotate a refresh token and issue a new token pair.

    Token rotation: the submitted refresh token is deleted from the DB before
    the new one is created. If the same token is submitted twice (e.g. a replay
    attack), the second call finds no row and raises ValueError → 401.

    Groups are re-queried so the new access token reflects any membership
    changes that happened since the last login.

    Args:
        db:            Active database session.
        refresh_token: The refresh token string from the client.

    Returns:
        Tuple (new_access_token, new_refresh_token).

    Raises:
        ValueError: If the token is not found in the DB (revoked or never issued).
        ValueError: If the JWT is expired or has an invalid signature.
        ValueError: If the user referenced in the token no longer exists.
    """
    token_entry = db.query(Token).filter(Token.refresh_token == refresh_token).first()
    if not token_entry:
        raise ValueError("Invalid refresh token")

    payload = decode_token(refresh_token)
    email = payload.get("sub")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise ValueError("User not found")

    # Rotate: delete old token immediately before issuing new one
    db.delete(token_entry)
    db.commit()

    groups = _get_user_groups(db, user.id)
    new_payload = {
        "sub":    user.email,
        "org_id": str(user.org_id) if user.org_id else None,
        "groups": groups,
    }

    new_access_token = create_access_token(new_payload)
    new_refresh_token = create_refresh_token({"sub": user.email})

    db.add(Token(user_id=user.id, refresh_token=new_refresh_token))
    db.commit()

    return new_access_token, new_refresh_token


def logout_user(db: Session, refresh_token: str):
    """
    Revoke a refresh token.

    Deletes the token row from the database. The client's refresh token
    becomes immediately unusable. Any access tokens already issued remain
    valid until they expire (they are stateless and cannot be revoked).

    Args:
        db:            Active database session.
        refresh_token: The refresh token string to revoke.

    Raises:
        ValueError: If the token is not found (already revoked or never issued).
    """
    token_entry = db.query(Token).filter(Token.refresh_token == refresh_token).first()
    if not token_entry:
        raise ValueError("Token not found or already revoked")

    db.delete(token_entry)
    db.commit()
