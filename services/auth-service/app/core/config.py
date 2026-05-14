"""
Auth Service — Configuration (app/core/config.py)

Purpose:
    Loads all environment-based configuration. Nothing is hardcoded here.
    All values come from environment variables (set via docker-compose or .env).

Settings:
    DATABASE_URL            — built from POSTGRES_* parts. Used by session.py.
    SECRET_KEY              — used to sign JWT tokens. Must stay secret.
                              MUST match JWT_SECRET_KEY in the gateway.
    ALGORITHM               — HS256 (hardcoded). Symmetric signing algorithm.
    ACCESS_TOKEN_EXPIRE_MINUTES  — how long access tokens live. Default: 120 min.
    REFRESH_TOKEN_EXPIRE_DAYS    — how long refresh tokens live. Default: 7 days.

Important:
    SECRET_KEY in this service and JWT_SECRET_KEY in the gateway must be identical.
    If they differ, the gateway will reject all tokens as "Invalid token".

In production:
    Replace env vars with AWS Secrets Manager, GCP Secret Manager, or Vault.
    Never hardcode or commit SECRET_KEY to git.
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'postgres')
    POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
    DATABASE_URL = (
        f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@"
        f"{POSTGRES_HOST}:{POSTGRES_PORT}/{os.getenv('POSTGRES_DB')}"
    )

    SECRET_KEY = os.getenv("SECRET_KEY")
    ALGORITHM = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 120))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

settings = Settings()