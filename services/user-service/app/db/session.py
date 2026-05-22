"""
DB Session (app/db/session.py)

Creates the SQLAlchemy engine and session factory.
get_db() is a FastAPI dependency — every route that needs DB gets a session
injected, and it's automatically closed when the request finishes.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
