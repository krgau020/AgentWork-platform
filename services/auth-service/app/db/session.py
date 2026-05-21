"""
db/session.py — Database engine and session factory.

Role in the system:
    Creates the SQLAlchemy engine (the connection pool to PostgreSQL) and
    provides get_db(), the FastAPI dependency used in every route that needs
    a database session.

    Every request that touches the database gets its own Session object,
    which is opened at the start of the request and closed in the finally
    block — even if the handler raises an exception. This guarantees that
    connections are returned to the pool and never leaked.

Design decisions:
    - pool_pre_ping=True tells SQLAlchemy to test each connection before
      using it by sending a cheap "SELECT 1". This prevents errors caused
      by stale connections that were idle long enough for the database or
      a network device to close them. Small overhead, big reliability gain
      in long-running Docker deployments.

    - SessionLocal is a factory (sessionmaker), not a session. Calling
      SessionLocal() produces a new Session object. Each call to get_db()
      creates one session for the lifetime of one HTTP request.

    - get_db() is a generator (uses yield). FastAPI's Depends() system
      understands generators — it runs the code before yield to set up,
      injects the yielded value into the route, then runs the code after
      yield (the finally block) when the request finishes.

Usage in routes:
    from app.db.session import get_db
    from fastapi import Depends

    @router.post("/example")
    def example(db: Session = Depends(get_db)):
        # db is a live SQLAlchemy session for this request only
        ...

Dependencies:
    - app.core.config.settings  →  DATABASE_URL
    - Used by: app.api.routes (via Depends), app.main (engine for startup check)
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Engine: manages the underlying connection pool to PostgreSQL.
# pool_pre_ping validates connections before use to avoid stale-connection errors.
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# Session factory — call SessionLocal() to get a new session object.
SessionLocal = sessionmaker(bind=engine)


def get_db():
    """
    FastAPI dependency that provides a database session per request.

    Opens a session, yields it to the route handler, then closes it
    in the finally block regardless of whether the handler succeeded
    or raised an exception. This ensures connections are never leaked.

    Yields:
        Session: An active SQLAlchemy ORM session bound to the PostgreSQL engine.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
