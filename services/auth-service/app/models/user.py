"""
Auth Service — User Model (app/models/user.py)

Purpose:
    SQLAlchemy model for the users table. Represents a registered user.
    Inherits from Base so SQLAlchemy tracks it for table creation.

Table: users
    id       — auto-incrementing primary key.
    email    — unique, indexed for fast lookups during login.
    password — Argon2-hashed. Never stored as plain text.
    role     — RBAC role. Defaults to "user". Can be set to "admin".
               Included in JWT access token payload so services know
               the user's role without a DB lookup.

Usage:
    Created in auth_service.create_user().
    Queried in auth_service.login_user() and refresh_access_token().
"""

from sqlalchemy import Column, Integer, String
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String, default="user")  # RBAC