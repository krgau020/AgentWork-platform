"""
GroupPolicy Join Model (app/models/group_policy.py)

Maps to the `group_policies` table — a many-to-many join table
between groups and policies.

One group can have many policies assigned to it.
One policy can be assigned to many groups (policies are reusable).

Example:
  group "admin"   → policies: ["full-access", "user-admin"]
  group "manager" → policies: ["document-read", "user-admin"]
  group "viewer"  → policies: ["document-read"]

  "user-admin" policy is reused across admin and manager groups.
  Creating it once and assigning to multiple groups is the PBAC advantage
  over RBAC where permissions are hardcoded inside each role.

Primary key is composite (group_id + policy_id) — the same pair cannot
be inserted twice, preventing duplicate assignments.
"""

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base


class GroupPolicy(Base):
    __tablename__ = "group_policies"

    group_id = Column(UUID(as_uuid=True), primary_key=True)
    policy_id = Column(UUID(as_uuid=True), primary_key=True)
