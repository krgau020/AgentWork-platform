"""
Application entry point.
Initializes FastAPI app and database.
"""

from fastapi import FastAPI
import time
import logging
from sqlalchemy import text
from app.api.routes import router
from app.db.base import Base
from app.db.session import engine
from app.models import user, token

log = logging.getLogger("auth-service")

app = FastAPI(title="Auth Service")

app.include_router(router, prefix="/auth", tags=["Auth"])


@app.get("/")
def root():
	return {"message": "Auth Service Running"}


def wait_for_db(connectable, retries=10, delay=2):
	"""Wait for the database to be available, with retries."""
	for attempt in range(1, retries + 1):
		try:
			with connectable.connect() as conn:
				conn.execute(text("SELECT 1"))
			log.info("Database is available")
			return True
		except Exception as exc:
			log.warning("DB not ready (attempt %d/%d): %s", attempt, retries, exc)
			time.sleep(delay)
	raise RuntimeError("Database not available after retries")


@app.on_event("startup")
def on_startup():
	# Wait for DB then create tables. In production prefer migrations (alembic).
	wait_for_db(engine, retries=10, delay=2)
	Base.metadata.create_all(bind=engine)