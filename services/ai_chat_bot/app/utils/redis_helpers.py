import redis.asyncio as redis
from redis.exceptions import RedisError

from app.core.config import REDIS_URL
from app.exceptions.memory_exceptions import RedisMemoryConnectionError

_redis_memory_client: redis.Redis | None = None


def get_redis_memory_client() -> redis.Redis:
    global _redis_memory_client
    if _redis_memory_client is None:
        if not REDIS_URL:
            raise RedisMemoryConnectionError("REDIS_URL is not configured")
        _redis_memory_client = redis.from_url(
            REDIS_URL,
            decode_responses=True,
            health_check_interval=30,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )
    return _redis_memory_client


async def close_redis_memory_client() -> None:
    global _redis_memory_client
    if _redis_memory_client is not None:
        await _redis_memory_client.aclose()
        _redis_memory_client = None


def redis_error_to_memory_error(exc: RedisError) -> RedisMemoryConnectionError:
    return RedisMemoryConnectionError("redis memory operation failed", details={"error_type": type(exc).__name__})
