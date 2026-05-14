"""
Auth Service — SQLAlchemy Declarative Base (app/db/base.py)

Purpose:
    Defines the Base class that all SQLAlchemy models inherit from.
    SQLAlchemy uses Base.metadata to track all registered models and
    create their corresponding database tables.

Usage:
    Every model file (user.py, token.py) imports Base from here and inherits:
        class User(Base): ...

    main.py calls Base.metadata.create_all(bind=engine) on startup to
    create all tables that don't yet exist in PostgreSQL.

In production:
    Replace create_all with Alembic migrations for version-controlled schema changes.
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()