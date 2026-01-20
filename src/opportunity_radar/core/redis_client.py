"""Redis client for caching and state management."""

import json
import logging
from typing import Any, Optional

import redis.asyncio as redis

from ..config import settings

logger = logging.getLogger(__name__)

# Global Redis connection pool
_redis_pool: Optional[redis.ConnectionPool] = None
_redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """Get Redis client instance with connection pooling."""
    global _redis_pool, _redis_client

    if _redis_client is None:
        _redis_pool = redis.ConnectionPool.from_url(
            settings.redis_url,
            max_connections=10,
            decode_responses=True,
        )
        _redis_client = redis.Redis(connection_pool=_redis_pool)

    return _redis_client


async def close_redis() -> None:
    """Close Redis connection pool."""
    global _redis_pool, _redis_client

    if _redis_client:
        await _redis_client.close()
        _redis_client = None

    if _redis_pool:
        await _redis_pool.disconnect()
        _redis_pool = None


class OAuthStateStore:
    """Redis-backed OAuth state storage for CSRF protection."""

    PREFIX = "oauth_state:"
    TTL_SECONDS = 300  # 5 minutes

    @classmethod
    async def store(cls, state: str, data: dict[str, Any]) -> bool:
        """Store OAuth state with expiration."""
        try:
            client = await get_redis()
            key = f"{cls.PREFIX}{state}"
            await client.setex(key, cls.TTL_SECONDS, json.dumps(data))
            return True
        except Exception as e:
            logger.error(f"Failed to store OAuth state: {e}")
            return False

    @classmethod
    async def get(cls, state: str) -> Optional[dict[str, Any]]:
        """Get OAuth state data."""
        try:
            client = await get_redis()
            key = f"{cls.PREFIX}{state}"
            data = await client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get OAuth state: {e}")
            return None

    @classmethod
    async def delete(cls, state: str) -> bool:
        """Delete OAuth state (consume it)."""
        try:
            client = await get_redis()
            key = f"{cls.PREFIX}{state}"
            result = await client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Failed to delete OAuth state: {e}")
            return False

    @classmethod
    async def get_and_delete(cls, state: str) -> Optional[dict[str, Any]]:
        """Atomically get and delete OAuth state (one-time use)."""
        try:
            client = await get_redis()
            key = f"{cls.PREFIX}{state}"
            # Use pipeline for atomic get+delete
            async with client.pipeline() as pipe:
                pipe.get(key)
                pipe.delete(key)
                results = await pipe.execute()

            data = results[0]
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get and delete OAuth state: {e}")
            return None
