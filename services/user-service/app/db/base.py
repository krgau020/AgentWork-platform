"""
SQLAlchemy Base (app/db/base.py)

All ORM model classes inherit from this Base.
SQLAlchemy uses it to track which classes are DB models
and to know which tables they map to.

Every model file imports Base from here — one shared base
across the whole service keeps everything consistent.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
