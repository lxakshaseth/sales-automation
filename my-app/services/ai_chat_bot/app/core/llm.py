import asyncio
import hashlib

import redis.asyncio as redis
from groq import AsyncGroq
from redis.exceptions import RedisError

from app.config.settings import settings
from app.core.config import REDIS_URL
from app.core.performance import measure
from app.utils.ttl_cache import TTLCache

ASK_FALLBACK_RESPONSE = "Thanks for reaching out. I will help you with sales automation details shortly."

_client: AsyncGroq | None = None
_redis_client: redis.Redis | None = None
_response_cache: TTLCache[str] = TTLCache(ttl_seconds=settings.ai_response_cache_ttl_seconds, max_entries=512)


def _cache_key(prompt: str) -> str:
    return hashlib.sha256(prompt.strip().lower().encode("utf-8")).hexdigest()


def _get_client() -> AsyncGroq:
    global _client
    if _client is None:
        _client = AsyncGroq(api_key=settings.groq_api_key)
    return _client


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
    global _client, _redis_client
    if _client is not None:
        await _client.close()
        _client = None
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
            cached = await asyncio.wait_for(client.get(f"ai:ask:{key}"), timeout=settings.redis_operation_timeout_seconds)
    except (TimeoutError, RedisError):
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
            await asyncio.wait_for(
                client.set(f"ai:ask:{key}", value, ex=settings.ai_response_cache_ttl_seconds),
                timeout=settings.redis_operation_timeout_seconds,
            )
    except (TimeoutError, RedisError):
        return


async def ask_llm(prompt: str) -> str:
    normalized = str(prompt or "").strip()
    if not normalized:
        return ASK_FALLBACK_RESPONSE

    if settings.mock_ai or settings.load_test_mode:
        return f"{ASK_FALLBACK_RESPONSE} You asked: {normalized[:120]}"

    key = _cache_key(normalized)
    cached = await _get_cached_response(key)
    if cached is not None:
        return cached

    if not settings.groq_api_key:
        return ASK_FALLBACK_RESPONSE

    try:
        async with measure("ai", "ask_llm", model=settings.groq_model):
            response = await asyncio.wait_for(
                _get_client().chat.completions.create(
                    model=settings.groq_model,
                    messages=[{"role": "user", "content": normalized}],
                    temperature=0.3,
                    max_tokens=300,
                ),
                timeout=settings.ai_request_timeout_seconds,
            )
    except Exception:
        return ASK_FALLBACK_RESPONSE

    content = response.choices[0].message.content or ASK_FALLBACK_RESPONSE
    result = content.strip()
    await _set_cached_response(key, result)
    return result
