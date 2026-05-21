"""
db/base.py — SQLAlchemy declarative base.

Role in the system:
    Defines the shared Base class that every ORM model in the auth service
    must inherit from. SQLAlchemy uses this Base to track all mapped classes
    and their associated table definitions via Base.metadata.

    This file has no application logic — it exists solely to avoid circular
    imports. If models imported session.py and session.py imported models,
    Python would deadlock on startup. Separating Base into its own file
    breaks that cycle:

        session.py  imports  base.py   (engine + sessionmaker)
        models/*.py import   base.py   (Base class)
        main.py     imports  both      (registers models, creates engine)

Design decisions:
    - declarative_base() is the classic SQLAlchemy pattern. The newer
      DeclarativeBase (SQLAlchemy 2.0) style can be adopted later without
      changing how models are defined.
    - Base.metadata is not used to create tables here. Table creation is
      handled by infra/postgres/init.sql via Docker on first container start,
      giving explicit control over the schema separate from the ORM.

Dependencies:
    - sqlalchemy.orm.declarative_base
    - Imported by: all files in app/models/, app/db/session.py, app/main.py
"""

from sqlalchemy.orm import declarative_base

# All ORM model classes inherit from this.
# SQLAlchemy registers them in Base.metadata automatically.
Base = declarative_base()
