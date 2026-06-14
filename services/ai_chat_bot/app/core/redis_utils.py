import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import TypeVar

import redis.asyncio as redis
from redis.exceptions import RedisError

from app.core.config import REDIS_OPERATION_TIMEOUT_SECONDS, REDIS_RETRY_ATTEMPTS, REDIS_RETRY_BACKOFF_SECONDS, REDIS_URL
from app.core.logger import log_error, log_event

T = TypeVar("T")


class RedisUnavailableError(RuntimeError):
    """Raised when Redis is unavailable after retries."""


async def redis_call(operation_name: str, operation: Callable[[], Awaitable[T]], *, timeout_seconds: float = REDIS_OPERATION_TIMEOUT_SECONDS) -> T:
    """Run a Redis operation with timeout, retry, backoff, and latency metrics."""
    backoffs = REDIS_RETRY_BACKOFF_SECONDS or (0.5, 1.0, 2.0)
    last_exc: Exception | None = None
    for attempt in range(1, REDIS_RETRY_ATTEMPTS + 1):
        started = time.perf_counter()
        try:
            result = await asyncio.wait_for(operation(), timeout=timeout_seconds)
            log_event(
                "redis_operation_completed",
                operation=operation_name,
                latency_ms=round((time.perf_counter() - started) * 1000, 2),
                attempt=attempt,
                retry_count=attempt - 1,
            )
            return result
        except (TimeoutError, RedisError) as exc:
            last_exc = exc
            log_error(
                "Redis operation failed",
                operation=operation_name,
                error_type=type(exc).__name__,
                attempt=attempt,
                retry_count=attempt - 1,
                timeout_seconds=timeout_seconds,
            )
            if attempt >= REDIS_RETRY_ATTEMPTS:
                break
            await asyncio.sleep(backoffs[min(attempt - 1, len(backoffs) - 1)])
    raise RedisUnavailableError(f"redis operation failed: {operation_name}") from last_exc


def create_redis_client() -> redis.Redis:
    """Create a Redis client with the shared reliability defaults."""
    if not REDIS_URL:
        raise RedisUnavailableError("REDIS_URL is not configured")
    return redis.from_url(
        REDIS_URL,
        decode_responses=True,
        health_check_interval=30,
        socket_connect_timeout=REDIS_OPERATION_TIMEOUT_SECONDS,
        socket_timeout=REDIS_OPERATION_TIMEOUT_SECONDS,
        retry_on_timeout=True,
    )


async def validate_redis_startup() -> bool:
    """Ping Redis at startup and return whether Redis-backed features are available."""
    if not REDIS_URL:
        log_error("Redis startup validation skipped", reason="REDIS_URL is not configured")
        return False
    client = create_redis_client()
    try:
        await redis_call("startup_ping", client.ping)
        log_event("redis_startup_validation_succeeded")
        return True
    except RedisUnavailableError as exc:
        log_error("Redis startup validation failed", error=str(exc))
        return False
    finally:
        await client.aclose()
