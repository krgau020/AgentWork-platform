"""
models/group.py — ORM model for the 'groups' table.

Role in the system:
    Groups are named collections of users within an organization. They are
    the unit of authorization in the AgentWork PBAC (Policy-Based Access
    Control) model:

        User → UserGroup → Group → GroupPolicy → Policy → PolicyStatement
                                                           (resource, action, effect)

    The gateway reads the 'groups' list from the JWT access token and uses
    it to decide whether to forward a request to a downstream service.

    At signup, every new organization automatically gets an "admin" group,
    and the signing-up user is added to it. Additional groups (e.g. "viewer",
    "operator") are created and managed through the user-service.

Columns:
    id          — UUID primary key.
    org_id      — FK to organizations.id. Groups are scoped to one org.
                  Two orgs can both have a group named "admin" — they are
                  independent records.
    name        — Group name within the org. Unique per org (enforced by
                  UniqueConstraint on org_id + name).
    description — Optional human-readable explanation of the group's purpose.
    created_at  — Audit timestamp.

Design decisions:
    - Group names are org-scoped, not globally unique. This allows every
      organization to have standard group names like "admin", "viewer",
      "operator" without conflict.
    - Policies are not stored on the group directly. The group_policies
      join table allows one group to have many policies and one policy to
      be shared across many groups.

Dependencies:
    - app.db.base.Base          →  SQLAlchemy declarative base
    - organizations table       →  FK on org_id
    - Used by: app.models.user_group (FK), app.services.auth_service
               (create default "admin" group on signup, query groups on login)
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from app.db.base import Base


class Group(Base):
    __tablename__ = "groups"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id      = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name        = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Group names must be unique within an organization
    __table_args__ = (UniqueConstraint("org_id", "name", name="uq_group_org_name"),)
