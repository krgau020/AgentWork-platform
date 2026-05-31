"""
Group Model (app/models/group.py)

Maps to the `groups` table. A group is a named collection of users
within one organization. Groups have policies. Users belong to groups.

org_id scope: groups are tenant-specific. Acme Corp's "admin" group
is a completely different record from Globex's "admin" group — same name,
different org_id, different UUID, different policies assigned.

The "admin" group is created automatically at signup by auth-service.
All other groups are created by the org admin via POST /api/v1/groups.

Uniqueness: group names are unique within an org (enforced in group_service.py),
but the same name can exist in different orgs.
"""

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base


class Group(Base):
    __tablename__ = "groups"

    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String, nullable=False)
    org_id = Column(UUID(as_uuid=True), nullable=False)
