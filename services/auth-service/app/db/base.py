"""
Base class for all database models.

Every model (User, Token, etc.) must inherit from this.
SQLAlchemy uses this to create tables.
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()