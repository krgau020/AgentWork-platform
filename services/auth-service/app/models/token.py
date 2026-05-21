"""
models/token.py — ORM model for the 'tokens' table.

Role in the system:
    Stores active refresh tokens. This is the server-side record that makes
    token revocation possible. When a user logs out, their refresh token row
    is deleted — even if the JWT itself hasn't expired yet, it can no longer
    be used to get a new access token.

    Access tokens are NOT stored here. They are stateless JWTs — validated
    by signature and expiry alone — and cannot be individually revoked before
    they expire. This is a deliberate trade-off: storing every access token
    would require a DB lookup on every API call, killing performance.

Columns:
    id            — UUID primary key.
    user_id       — FK to users.id. Identifies which user owns this token.
                    Allows querying "all active sessions for user X" in the future.
    refresh_token — The full JWT string. Unique constraint ensures the same
                    token cannot be stored twice (guards against race conditions
                    in token rotation).
    created_at    — When the token was issued. Useful for auditing active sessions
                    and for future cleanup jobs that expire very old tokens.

Design decisions:
    - Token rotation is implemented: on every /refresh call, the old row is
      deleted and a new row is inserted. This means a stolen refresh token
      can only be used once before it's rotated away.
    - No 'expires_at' column yet. The expiry is encoded in the JWT itself
      (decode_token checks it). A cleanup job to remove expired rows from
      the DB is a future improvement.
    - One user can have multiple active tokens (multiple devices/sessions).
      Deleting all tokens for a user_id is a "logout everywhere" operation.

Dependencies:
    - app.db.base.Base  →  SQLAlchemy declarative base
    - users table       →  FK constraint on user_id
    - Used by: app.services.auth_service (create, delete on rotation/logout)
"""

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from app.db.base import Base


class Token(Base):
    __tablename__ = "tokens"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id       = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    refresh_token = Column(String, unique=True, nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow, nullable=False)
