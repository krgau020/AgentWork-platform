"""
Rate Limiter (app/core/rate_limiter.py)

Purpose:
    Per-org rate limiting using Redis as a shared counter store.
    Enforces a maximum number of requests per org per time window across
    all gateway instances.

How it works:
    Every protected request carries x-org-id (extracted from the JWT by the
    gateway). This module increments a Redis counter keyed by org_id on every
    request. If the counter exceeds RATE_LIMIT within WINDOW_SECONDS, the
    request is rejected with 429.

    Redis key pattern:  ratelimit:{org_id}
    Key TTL:            60 seconds (auto-expires — no manual cleanup needed)
    Limit:              1000 requests per 60-second window per org

    Pipeline:
        INCR ratelimit:{org_id}   → atomically increment, returns new count
        EXPIRE ratelimit:{org_id} → set TTL only when key is first created

    The pipeline is atomic — no race condition between INCR and EXPIRE.

Fail-open design:
    If Redis is unavailable (container restart, network blip), the check
    returns True (allowed). The platform continues to serve requests rather
    than going down because of a missing cache layer.
    Log the error so the team knows Redis is unhealthy.

FastAPI integration:
    rate_limit() is a FastAPI dependency that:
      1. Calls get_token_payload() — validates the JWT (so token check runs first)
      2. Extracts org_id from the payload
      3. Checks the Redis counter
      4. Raises 429 if exceeded, otherwise returns the payload unchanged

    Protected routes use Depends(rate_limit) instead of Depends(get_token_payload).
    The dependency chain is: rate_limit → get_token_payload → HTTP request.
    Token validation always runs; rate check runs after a valid token is confirmed.

Usage:
    from app.core.rate_limiter import rate_limit
    @router.get("/api/v1/users")
    async def users(payload: dict = Depends(rate_limit)):
        ...
"""

import logging

import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, Request

from app.core.config import settings
from app.core.security import get_token_payload

logger = logging.getLogger(__name__)

RATE_LIMIT = 1000
WINDOW_SECONDS = 60

_redis_client: aioredis.Redis | None = None


def _get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


async def rate_limit(
    request: Request,
    payload: dict = Depends(get_token_payload),
) -> dict:
    """
    FastAPI dependency. Validates JWT (via get_token_payload), then enforces
    per-org rate limit. Returns the JWT payload on success.
    Raises 429 if the org has exceeded RATE_LIMIT requests in WINDOW_SECONDS.
    Fails open if Redis is unreachable.
    """
    org_id = payload.get("org_id", "unknown")
    key = f"ratelimit:{org_id}"

    try:
        r = _get_redis()
        pipe = r.pipeline()
        pipe.incr(key)
        pipe.expire(key, WINDOW_SECONDS)
        results = await pipe.execute()
        count = results[0]

        if count > RATE_LIMIT:
            raise HTTPException(
                status_code=429,
                detail={
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "message": f"Rate limit of {RATE_LIMIT} requests per minute exceeded for this organization.",
                },
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Rate limiter Redis error (fail-open): %s", exc)

    return payload
