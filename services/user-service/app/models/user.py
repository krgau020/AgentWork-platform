"""
User Model (app/models/user.py)

Maps to the `users` table. User-service never creates users — auth-service
does that at signup. User-service only reads user data and manages their
group memberships.

Columns deliberately excluded here:
  password_hash — user-service never reads or writes passwords.
  Only auth-service touches that column.

org_id is the tenant key. Every query in user_service.py includes
.filter(User.org_id == org_id) — a user from one org is completely
invisible to another org even if they know the UUID.
"""

from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True)
    email = Column(String, nullable=False, unique=True)
    org_id = Column(UUID(as_uuid=True), nullable=False)
    is_active = Column(Boolean, default=True)
