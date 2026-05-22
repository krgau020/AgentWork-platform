"""
UserGroup Join Model (app/models/user_group.py)

Maps to the `user_groups` table — a many-to-many join table
between users and groups.

One user can belong to many groups.
One group can have many users.

Example:
  alice → groups: [admin, billing]
  bob   → groups: [developer]
  carol → groups: [manager, developer]

  Alice inherits permissions from both admin and billing groups.
  Carol inherits permissions from both manager and developer groups.

Created entries:
  At signup — auth-service inserts one row: { user_id: new_user, group_id: admin_group }
  After that — user-service manages all other assignments via:
    POST   /api/v1/users/{id}/groups  → add_user_to_group
    DELETE /api/v1/users/{id}/groups/{group_id} → remove_user_from_group

Primary key is composite (user_id + group_id) — prevents a user from
being added to the same group twice.
"""

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base


class UserGroup(Base):
    __tablename__ = "user_groups"

    user_id = Column(UUID(as_uuid=True), primary_key=True)
    group_id = Column(UUID(as_uuid=True), primary_key=True)
