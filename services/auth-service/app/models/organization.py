"""
models/organization.py — ORM model for the 'organizations' table.

Role in the system:
    Organizations are the top-level multi-tenancy boundary in the AgentWork
    platform. Every user belongs to exactly one organization. Groups, policies,
    and access rules are all scoped to an organization, so data from one tenant
    is never visible to another.

    An organization is created automatically when the first user signs up
    (via auth_service.create_user). Future phases will add an admin UI for
    managing organization settings.

Columns:
    id         — UUID primary key.
    name       — Human-readable display name (e.g. "Acme Corp").
    slug       — URL-safe, lowercase, hyphenated version of the name
                 (e.g. "acme-corp"). Must be globally unique. Used in future
                 sub-domain routing (acme-corp.agentwork.io) and API paths.
    is_active  — Soft-disable flag for the whole organization. Setting this
                 to False effectively locks out all users of that org without
                 deleting any data.
    created_at — Audit timestamp.

Design decisions:
    - Slug uniqueness is enforced at both the DB level (UNIQUE constraint in
      init.sql) and the application level (auth_service checks before insert)
      to give a clean error message rather than a raw DB exception.
    - No 'owner_id' column yet. Ownership/billing will be modeled in a future
      phase when the platform supports org management through the UI.

Dependencies:
    - app.db.base.Base  →  SQLAlchemy declarative base
    - Used by: app.models.user (FK), app.models.group (FK),
               app.services.auth_service (create on signup)
"""

from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from app.db.base import Base


class Organization(Base):
    __tablename__ = "organizations"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name       = Column(String(255), nullable=False)
    slug       = Column(String(100), unique=True, nullable=False)
    is_active  = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
