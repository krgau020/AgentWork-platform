"""
Alembic Migration Environment (alembic/env.py)

This file is the bridge between Alembic and the database.
It runs every time you invoke any alembic command.

How the database URL is resolved:
    1. Reads individual POSTGRES_* environment variables (same ones used by
       the auth-service config) and builds the URL.
    2. Falls back to the sqlalchemy.url in alembic.ini if env vars are absent
       (useful when running alembic locally without Docker env vars).

Why not import app.core.config:
    Alembic env.py runs outside the FastAPI app context — importing settings
    would pull in all service dependencies. Reading os.environ directly is
    simpler and avoids import-chain issues.

Online vs offline mode:
    Online  — connects to the DB and runs migrations against a live connection.
              This is the normal mode (alembic upgrade head).
    Offline — generates SQL to stdout without connecting.
              Used to preview what SQL Alembic would run (alembic upgrade head --sql).
"""

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Build DATABASE_URL from environment variables (same pattern as auth-service)
_user = os.environ.get("POSTGRES_USER", "admin")
_password = os.environ.get("POSTGRES_PASSWORD", "admin")
_host = os.environ.get("POSTGRES_HOST", "localhost")
_port = os.environ.get("POSTGRES_PORT", "5432")
_db = os.environ.get("POSTGRES_DB", "agentwork")
_db_url = f"postgresql://{_user}:{_password}@{_host}:{_port}/{_db}"

config.set_main_option("sqlalchemy.url", _db_url)

# target_metadata = None → no autogenerate (migrations are written manually)
# To enable autogenerate, import Base and set: target_metadata = Base.metadata
target_metadata = None


def run_migrations_offline() -> None:
    """Generate SQL without a live DB connection (--sql flag)."""
    context.configure(
        url=_db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live database connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
