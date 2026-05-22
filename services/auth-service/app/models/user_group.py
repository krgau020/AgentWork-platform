"""
models/user_group.py — ORM model for the 'user_groups' join table.

Role in the system:
    This is the many-to-many association table between users and groups.
    A user can belong to multiple groups (e.g. "admin" and "billing").
    A group can have multiple users.

    At login, auth_service queries this table joined with the groups table
    to collect the group names for the JWT payload:

        SELECT groups.name
        FROM groups
        JOIN user_groups ON groups.id = user_groups.group_id
        WHERE user_groups.user_id = <user.id>

    The gateway then reads those group names from the token to make
    authorization decisions without an additional database call.

Columns (composite primary key):
    user_id   — FK to users.id. The user being assigned to a group.
    group_id  — FK to groups.id. The group being assigned to the user.

    Together (user_id, group_id) form the primary key, which automatically
    prevents duplicate assignments (a user cannot be added to the same
    group twice).

Design decisions:
    - No SQLAlchemy relationship() is defined here. Relationships add
      convenience methods (user.groups, group.users) but also implicit
      queries that are harder to reason about. Explicit JOIN queries in
      auth_service._get_user_groups() are preferred for clarity.
    - No 'assigned_at' or 'assigned_by' audit columns yet. These would
      be useful for compliance logging and are a future improvement.

Dependencies:
    - app.db.base.Base  →  SQLAlchemy declarative base
    - users table       →  FK on user_id
    - groups table      →  FK on group_id
    - Used by: app.services.auth_service (insert on signup, join query on login)
"""

from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base


class UserGroup(Base):
    __tablename__ = "user_groups"

    user_id  = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    group_id = Column(UUID(as_uuid=True), ForeignKey("groups.id"), primary_key=True)
