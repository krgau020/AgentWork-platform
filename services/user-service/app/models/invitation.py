"""
Invitation Model (app/models/invitation.py)

Maps to the `invitations` table. An invitation is a one-time-use token
that allows a specific email address to join an organization in a pre-assigned
group without going through the normal public signup flow.

Flow — how this model is used:
    1. Admin calls POST /api/v1/orgs/{org_id}/invites with {email, group_id}
    2. invite_service creates an Invitation row with a random token + 7-day expiry
    3. The token is returned to the admin, who shares it with the invitee
    4. Invitee calls POST /api/v1/auth/accept-invite with {invite_token, password}
    5. auth-service reads this row, validates token and expiry, creates the User,
       adds them to group_id, then deletes this row (one-time-use enforced by DELETE)

Columns:
    id         — UUID primary key assigned by Python before INSERT.
    org_id     — Which organization the invitee will join. Carried into the new
                 User row at accept time so the user's org_id is set automatically.
    email      — The intended recipient. Stored for display; not enforced as unique
                 here — auth-service validates uniqueness against the users table
                 when the invite is accepted.
    group_id   — The group the invitee will be placed into on acceptance.
                 invite_service validates this group belongs to org_id before saving.
    token      — Cryptographically random opaque string (secrets.token_urlsafe(32)).
                 NOT a JWT — stored and looked up by value in the DB.
    expires_at — UTC timestamp, 7 days from creation. Invitations past this time
                 are rejected and deleted by auth-service on the next accept attempt.
    created_at — Audit timestamp. Set once at INSERT, never updated.

Design decisions:
    - No ForeignKey declarations on org_id or group_id at the ORM level because
      this model is shared between two services (user-service and auth-service)
      and FK enforcement is already handled by the DB via init.sql.
    - One-time use is enforced by DELETE (not a 'used' flag) so stale rows never
      accumulate — once accepted, the row is gone.

Dependencies:
    - app.db.base.Base  →  SQLAlchemy declarative base
    - Used by: app.services.invite_service (user-service),
               app.services.auth_service (auth-service accept_invite)
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
