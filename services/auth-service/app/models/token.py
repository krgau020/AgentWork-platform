"""
Auth Service — Token Model (app/models/token.py)

Purpose:
    SQLAlchemy model for the tokens table. Stores refresh tokens so they
    can be revoked before their natural expiry.

Table: tokens
    id            — auto-incrementing primary key.
    user_id       — references the user this token belongs to.
    refresh_token — the full JWT refresh token string. Unique constraint
                    prevents the same token being stored twice.

How revocation works:
    When a user logs in, their refresh_token is saved here.
    On /auth/refresh: service checks this table first. If the token is not
    found, it is rejected — even if the JWT itself is still valid.
    To revoke a session: delete the row. That user must log in again.

Note:
    Access tokens are NOT stored here. They are stateless — they expire
    on their own after 120 minutes. Only refresh tokens need DB storage
    because they live for 7 days and need manual revocation capability.
"""

from sqlalchemy import Column, Integer, String
from app.db.base import Base

class Token(Base):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    refresh_token = Column(String, unique=True)