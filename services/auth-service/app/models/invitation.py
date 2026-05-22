"""
Invitation Model (app/models/invitation.py)

Maps to the `invitations` table. This is the auth-service copy of the model —
the table is shared between user-service (creates invites) and auth-service
(reads and consumes invites when a user accepts).

Role in the auth-service:
    auth-service's accept_invite() function is the only consumer of this model.
    It looks up the Invitation by token, validates expiry, creates the User and
    UserGroup rows, then deletes this row. After deletion the token can never
    be reused — one-time-use is enforced by the DELETE.

Columns:
    id         — UUID primary key.
    org_id     — Copied into the new User.org_id when the invite is accepted.
    email      — The intended recipient's email. auth-service checks that no
                 existing user has this email before creating a new account.
    group_id   — The group the new user is placed into after account creation.
    token      — Opaque random string (not a JWT). Looked up by exact value.
    expires_at — UTC timestamp with timezone. Compared against datetime.now(utc)
                 at accept time. Expired invitations are rejected and deleted.
    created_at — Audit timestamp.

Design note:
    No ORM-level ForeignKey declarations — FK constraints are owned by the DB
    (init.sql). Declaring them in both services would require both services to
    also declare the referenced models, which is unnecessary coupling.

Dependencies:
    - app.db.base.Base  →  SQLAlchemy declarative base
    - Used by: app.services.auth_service (accept_invite function)
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class Invitation(Base):
    __tablename__ = "invitations"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id     = Column(UUID(as_uuid=True), nullable=False)
    email      = Column(String(255), nullable=False)
    group_id   = Column(UUID(as_uuid=True), nullable=False)
    token      = Column(String, nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
