import json
import logging
from typing import Any

import redis.asyncio as redis
from redis.exceptions import RedisError

from app.core.config import REDIS_MEMORY_TTL_SECONDS
from app.core.redis_utils import RedisUnavailableError, create_redis_client, redis_call

logger = logging.getLogger(__name__)

MEMORY_KEY_PREFIX = "agent:memory"

_redis_client: redis.Redis | None = None


class MemoryStoreError(RuntimeError):
    """Raised when chatbot memory cannot be read from or written to Redis."""


def _memory_key(user_id: str) -> str:
    """Namespace memory keys so they do not collide with other Redis data."""
    if not user_id or not str(user_id).strip():
        raise ValueError("user_id is required")

    return f"{MEMORY_KEY_PREFIX}:{str(user_id).strip()}"


def _get_redis_client() -> redis.Redis:
    """
    Lazily create one Redis client per process.

    redis.asyncio clients manage a reusable connection pool internally, which avoids
    opening a new TCP connection for every chatbot message.
    """
    global _redis_client

    if _redis_client is None:
        _redis_client = create_redis_client()

    return _redis_client


def _serialize_history(history: list[Any]) -> str:
    """Serialize conversation history to JSON with clear failures for bad payloads."""
    try:
        return json.dumps(history, ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("message must be JSON serializable") from exc


def _deserialize_history(raw_value: str | bytes | None) -> list[Any]:
    """Convert Redis data back into a Python list, treating missing keys as empty memory."""
    if raw_value is None:
        return []

    if isinstance(raw_value, bytes):
        raw_value = raw_value.decode("utf-8")

    try:
        history = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise MemoryStoreError("stored memory is not valid JSON") from exc

    if not isinstance(history, list):
        raise MemoryStoreError("stored memory must be a JSON list")

    return history


async def save_memory(user_id: str, message: Any) -> list[Any]:
    """
    Replace a user's short-term conversation memory.

    Pass either a single message object or a full list of message objects. The stored
    value is always a JSON list and expires after seven days by default.
    """
    history = message if isinstance(message, list) else [message]
    payload = _serialize_history(history)

    try:
        await redis_call(
            "memory_save",
            lambda: _get_redis_client().set(
                _memory_key(user_id),
                payload,
                ex=REDIS_MEMORY_TTL_SECONDS,
            ),
        )
    except (RedisUnavailableError, RedisError) as exc:
        logger.exception("Failed to save memory for user_id=%s", user_id)
        raise MemoryStoreError("failed to save memory") from exc

    return history


async def get_memory(user_id: str) -> list[Any]:
    """Fetch a user's conversation memory as a JSON-deserialized list."""
    try:
        raw_value = await redis_call("memory_get", lambda: _get_redis_client().get(_memory_key(user_id)))
    except (RedisUnavailableError, RedisError) as exc:
        logger.exception("Failed to get memory for user_id=%s", user_id)
        raise MemoryStoreError("failed to get memory") from exc

    return _deserialize_history(raw_value)


async def append_memory(user_id: str, message: Any) -> list[Any]:
    """
    Append one message to a user's memory and refresh the TTL.

    This read-modify-write pattern is simple and works well for typical AI chatbot
    turns. For extremely high write concurrency per user, wrap it in a Redis lock or
    Lua script to make appends strictly atomic.
    """
    key = _memory_key(user_id)

    try:
        client = _get_redis_client()
        raw_value = await redis_call("memory_append_get", lambda: client.get(key))
        history = _deserialize_history(raw_value)
        history.append(message)
        await redis_call("memory_append_set", lambda: client.set(key, _serialize_history(history), ex=REDIS_MEMORY_TTL_SECONDS))
    except (RedisUnavailableError, RedisError) as exc:
        logger.exception("Failed to append memory for user_id=%s", user_id)
        raise MemoryStoreError("failed to append memory") from exc

    return history


async def clear_memory(user_id: str) -> bool:
    """Delete a user's memory. Returns True when a key was removed."""
    try:
        deleted_count = await redis_call("memory_clear", lambda: _get_redis_client().delete(_memory_key(user_id)))
    except (RedisUnavailableError, RedisError) as exc:
        logger.exception("Failed to clear memory for user_id=%s", user_id)
        raise MemoryStoreError("failed to clear memory") from exc

    return deleted_count > 0


async def close_memory_client() -> None:
    """Close the shared Redis connection pool during application shutdown or tests."""
    global _redis_client

    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
