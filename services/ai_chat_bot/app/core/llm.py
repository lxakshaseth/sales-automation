import hashlib

import redis.asyncio as redis
from redis.exceptions import RedisError

from app.config.settings import settings
from app.core.config import REDIS_URL
from app.core.performance import measure
from app.core.redis_utils import RedisUnavailableError, redis_call
from app.utils.ttl_cache import TTLCache

ASK_FALLBACK_RESPONSE = "Thanks for reaching out. I will help you with sales automation details shortly."

_redis_client: redis.Redis | None = None
_response_cache: TTLCache[str] = TTLCache(ttl_seconds=settings.ai_response_cache_ttl_seconds, max_entries=512)


def _cache_key(prompt: str) -> str:
    return hashlib.sha256(prompt.strip().lower().encode("utf-8")).hexdigest()


def _get_redis_client() -> redis.Redis | None:
    global _redis_client
    if not REDIS_URL:
        return None
    if _redis_client is None:
        _redis_client = redis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=settings.redis_operation_timeout_seconds,
            socket_timeout=settings.redis_operation_timeout_seconds,
            health_check_interval=30,
            retry_on_timeout=True,
        )
    return _redis_client


async def close_llm_client() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None


async def _get_cached_response(key: str) -> str | None:
    cached = _response_cache.get(key)
    if cached is not None:
        return cached
    client = _get_redis_client()
    if client is None:
        return None
    try:
        async with measure("redis", "ask_llm.cache_get"):
            cached = await redis_call("ask_llm_cache_get", lambda: client.get(f"ai:ask:{key}"), timeout_seconds=settings.redis_operation_timeout_seconds)
    except (RedisUnavailableError, RedisError):
        return None
    if cached:
        _response_cache.set(key, cached, ttl_seconds=settings.ai_response_cache_ttl_seconds)
    return cached


async def _set_cached_response(key: str, value: str) -> None:
    _response_cache.set(key, value, ttl_seconds=settings.ai_response_cache_ttl_seconds)
    client = _get_redis_client()
    if client is None:
        return
    try:
        async with measure("redis", "ask_llm.cache_set"):
            await redis_call(
                "ask_llm_cache_set",
                lambda: client.set(f"ai:ask:{key}", value, ex=settings.ai_response_cache_ttl_seconds),
                timeout_seconds=settings.redis_operation_timeout_seconds,
            )
    except (RedisUnavailableError, RedisError):
        return


async def ask_llm(prompt: str) -> str:
    normalized = str(prompt or "").strip()
    if not normalized:
        return ASK_FALLBACK_RESPONSE

    key = _cache_key(normalized)
    cached = await _get_cached_response(key)
    if cached is not None:
        return cached

    try:
        from app.security import secure_process_request

        async with measure("ai", "ask_llm.secured", model=settings.groq_model):
            secured = await secure_process_request(
                {
                    "user_query": normalized,
                    "tenant_id": "default",
                    "channel": "ask_llm",
                    "metadata": {"tenant_id": "default", "entrypoint": "ask_llm"},
                    "timeout_seconds": settings.ai_request_timeout_seconds,
                }
            )
    except Exception:
        return ASK_FALLBACK_RESPONSE

    result = secured.response.strip() or ASK_FALLBACK_RESPONSE
    await _set_cached_response(key, result)
    return result
