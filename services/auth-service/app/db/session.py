"""
Auth Service — Database Session Factory (app/db/session.py)

Purpose:
    Creates the SQLAlchemy engine (connection to PostgreSQL) and the
    SessionLocal factory used to create per-request DB sessions.

Key components:
    engine        — the database connection. Built from DATABASE_URL in config.py.
                    pool_pre_ping=True checks if the connection is alive before use,
                    preventing errors from stale/timed-out connections.
    SessionLocal  — a factory. Calling SessionLocal() creates a new DB session.
                    Each API request gets its own session (created in get_db() in routes.py).

Session lifecycle (in routes.py get_db()):
    db = SessionLocal()  → open session
    yield db             → give to route handler
    db.close()           → always close after request, even on error

NullPool note:
    Not used here — standard connection pooling is active.
    NullPool would disable pooling (useful in serverless/Lambda environments).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from app.core.config import settings

# Use pool_pre_ping to avoid stale/closed connections in long-running apps
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)