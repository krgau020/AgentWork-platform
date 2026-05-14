"""
Gateway Configuration (app/core/config.py)

Purpose:
    Loads all environment-based configuration for the gateway. No secrets or
    URLs are hardcoded here — everything is read from environment variables.

Settings loaded:
    JWT_SECRET_KEY   — used to verify incoming JWT tokens. MUST match the
                       SECRET_KEY used by auth-service to sign tokens.
                       If they differ, all token validation fails with "Invalid token".
    AUTH_SERVICE_URL — internal Docker URL for auth-service.
                       Default: http://auth-service:8001 (Docker service name).

How config is loaded:
    .env file → docker-compose (env_file:) → container env → os.getenv() here

In production:
    Replace .env with AWS Secrets Manager, HashiCorp Vault, or GCP Secret Manager.
    Never commit .env to git.
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    AUTH_SERVICE_URL = os.getenv(
        "AUTH_SERVICE_URL",
        "http://auth-service:8001"
    )

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecret")

settings = Settings()