"""
core/config.py — Central configuration loader.

Role in the system:
    Single source of truth for all runtime configuration. Every value that
    might differ between environments (dev, staging, prod) lives here and
    is read from environment variables — never hardcoded in application code.

    In Docker, environment variables are injected via docker-compose.yml.
    Locally, they are loaded from the .env file via python-dotenv.

Design decisions:
    - Uses a plain class (not a Pydantic BaseSettings model) to keep
      dependencies minimal. If stricter validation is needed in the future
      (e.g., fail fast when SECRET_KEY is missing), this is the right place
      to add it.
    - DATABASE_URL is assembled from parts (USER, PASSWORD, HOST, PORT, DB)
      rather than a single connection string so that each component can be
      overridden independently in different environments.
    - POSTGRES_HOST defaults to "postgres" — the Docker service name. This
      allows the service to connect inside Docker without any override while
      still being overridable for local development (e.g., "localhost").

Environment variables required:
    POSTGRES_USER           Database user (default: none — must be set)
    POSTGRES_PASSWORD       Database password (default: none — must be set)
    POSTGRES_DB             Database name (default: none — must be set)
    POSTGRES_HOST           Database host (default: "postgres")
    POSTGRES_PORT           Database port (default: "5432")
    SECRET_KEY              JWT signing key (default: none — must be set)
    ACCESS_TOKEN_EXPIRE_MINUTES   Access token TTL in minutes (default: 120)
    REFRESH_TOKEN_EXPIRE_DAYS     Refresh token TTL in days (default: 7)

Dependencies:
    - python-dotenv  →  loads .env file in local/dev environments
    - Used by: app.core.security, app.db.session
"""

import os
from dotenv import load_dotenv

# Load .env file if present (dev/local only — in Docker, env vars come from compose)
load_dotenv()


class Settings:
    """
    Container for all application configuration values.

    Reads from environment variables at class definition time (not at
    instantiation), so all values are available as class attributes on
    the singleton `settings` object imported by other modules.
    """

    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "postgres")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")

    DATABASE_URL: str = (
        f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@"
        f"{POSTGRES_HOST}:{POSTGRES_PORT}/{os.getenv('POSTGRES_DB')}"
    )

    # JWT signing key — keep this secret and rotate it if compromised.
    # All tokens signed with the old key become invalid after rotation.
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 120))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))


# Module-level singleton — import this in all other modules:
#   from app.core.config import settings
settings = Settings()
