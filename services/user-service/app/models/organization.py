"""
Organization Model (app/models/organization.py)

Maps to the `organizations` table created by infra/postgres/init.sql.
User-service NEVER creates or deletes organizations — that is done by
auth-service atomically during signup (one org per signup).

This model is used read-only: to fetch org details when an admin calls
GET /api/v1/orgs/{id}.

Why org_id comes from the header, not this table:
  The gateway decodes the JWT and sends x-org-id. We trust that header.
  We only hit this table when the client explicitly requests org details.
"""

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String, nullable=False, unique=True)
