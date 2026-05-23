"""
Policy Cache (app/core/cache.py)

Purpose:
    Caches the resolved policy list for a user in Redis to avoid repeating
    the 4-table DB join (user_groups → group_policies → policies → policy_statements)
    on every GET /api/v1/users/{user_id}/policies call.

Cache key:  policy:{user_id}
TTL:        300 seconds (5 minutes)
Value:      JSON-serialised list of policy dicts

Invalidation:
    The cache is explicitly deleted when a user's group membership changes:
        - add_user_to_group    → invalidate_policy_cache(user_id)
        - remove_user_from_group → invalidate_policy_cache(user_id)
    For policy/statement changes (group-level): TTL handles staleness.
    Max staleness is 5 minutes — acceptable for Phase 4.

Fail-open:
    All Redis errors are caught and logged. On cache read failure the
    DB query runs normally. On cache write failure the result is still
    returned to the client — just not cached. The service never goes
    down because of a Redis issue.
"""

import json
import logging

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)

POLICY_TTL = 300

_redis_client: aioredis.Redis | None = None


def _get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


async def get_policy_cache(user_id: str) -> list | None:
    """Return cached policies for user_id, or None on miss/error."""
    try:
        data = await _get_redis().get(f"policy:{user_id}")
        if data:
            return json.loads(data)
    except Exception as exc:
        logger.warning("Policy cache GET error (fail-open): %s", exc)
    return None


async def set_policy_cache(user_id: str, policies: list) -> None:
    """Store policies for user_id with POLICY_TTL expiry."""
    try:
        await _get_redis().set(f"policy:{user_id}", json.dumps(policies), ex=POLICY_TTL)
    except Exception as exc:
        logger.warning("Policy cache SET error (fail-open): %s", exc)


async def invalidate_policy_cache(user_id: str) -> None:
    """Delete cached policies for user_id — call when group membership changes."""
    try:
        await _get_redis().delete(f"policy:{user_id}")
    except Exception as exc:
        logger.warning("Policy cache DELETE error (fail-open): %s", exc)
