"""
Gateway Configuration (app/core/config.py)

Purpose:
    Reads environment variables from .env and makes them available throughout
    the gateway as a single typed settings object.

Why Pydantic BaseSettings:
    Reads from .env automatically, validates required fields at startup,
    and is type-safe — SECRET_KEY is guaranteed to be a str, never None.
    One import (settings) gives access to all config values anywhere in the code.

Variables:
    SECRET_KEY       — JWT signing secret. Must exactly match auth-service's
                       SECRET_KEY. If they differ, every token is rejected as
                       invalid — even perfectly good ones.
    ALGORITHM        — JWT signing algorithm. HS256 matches auth-service.
    AUTH_SERVICE_URL — Internal Docker URL for auth-service.
                       "http://auth-service:8001" uses Docker's internal DNS —
                       the name "auth-service" resolves to the container's IP.
    USER_SERVICE_URL — Internal Docker URL for user-service.

Usage:
    from app.core.config import settings
    settings.SECRET_KEY         → "supersecret"
    settings.AUTH_SERVICE_URL   → "http://auth-service:8001"
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    AUTH_SERVICE_URL: str
    USER_SERVICE_URL: str
    REDIS_URL: str = "redis://redis:6379"

    class Config:
        env_file = ".env"


settings = Settings()
