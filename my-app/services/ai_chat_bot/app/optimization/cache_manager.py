from typing import Any

import redis.asyncio as redis
from redis.exceptions import RedisError

from app.core.config import REDIS_URL
from app.core.logger import log_error, log_event
from app.exceptions.optimization_exceptions import CacheOperationError
from app.models.cache_models import CacheResult
from app.utils.cache_helpers import build_cache_key, stable_json_dumps


class CacheManager:
    """Redis-backed cache manager with local fallback for tests and degraded mode."""

    _local_cache: dict[str, Any] = {}

    def __init__(self, *, redis_client: redis.Redis | None = None, enable_in_memory_fallback: bool = True) -> None:
        self.redis_client = redis_client
        self.enable_in_memory_fallback = enable_in_memory_fallback

    def _client(self) -> redis.Redis | None:
        if self.redis_client is not None:
            return self.redis_client
        if not REDIS_URL:
            return None
        self.redis_client = redis.from_url(
            REDIS_URL,
            decode_responses=True,
            health_check_interval=30,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )
        return self.redis_client

    async def cache_retrieval(self, query: str, results: Any, *, ttl_seconds: int = 900, metadata: dict | None = None) -> CacheResult:
        key = build_cache_key("retrieval", {"query": query, "metadata": metadata or {}})
        return await self.set(key, results, namespace="retrieval", ttl_seconds=ttl_seconds)

    async def fetch_cached_retrieval(self, query: str, *, metadata: dict | None = None) -> CacheResult:
        key = build_cache_key("retrieval", {"query": query, "metadata": metadata or {}})
        return await self.get(key, namespace="retrieval")

    async def cache_embedding(self, text: str, embedding: list[float], *, model_name: str | None = None, ttl_seconds: int = 86400) -> CacheResult:
        key = build_cache_key("embedding", {"text": text, "model_name": model_name})
        return await self.set(key, embedding, namespace="embedding", ttl_seconds=ttl_seconds)

    async def fetch_cached_embedding(self, text: str, *, model_name: str | None = None) -> CacheResult:
        key = build_cache_key("embedding", {"text": text, "model_name": model_name})
        return await self.get(key, namespace="embedding")

    async def invalidate_cache(self, namespace: str, value: Any | None = None) -> CacheResult:
        key_or_pattern = build_cache_key(namespace, value) if value is not None else f"opt:v1:{namespace}:*"
        try:
            client = self._client()
            if client is None:
                deleted = self._delete_local(key_or_pattern)
            elif "*" in key_or_pattern:
                keys = [key async for key in client.scan_iter(match=key_or_pattern, count=200)]
                deleted = await client.delete(*keys) if keys else 0
            else:
                deleted = await client.delete(key_or_pattern)
            log_event("optimization_cache_invalidated", namespace=namespace, deleted=int(deleted))
            return CacheResult(success=True, hit=False, key=key_or_pattern, namespace=None, value={"deleted": int(deleted)})
        except RedisError as exc:
            log_error("Optimization cache invalidation failed", namespace=namespace, error_type=type(exc).__name__)
            raise CacheOperationError("cache invalidation failed") from exc

    async def get(self, key: str, *, namespace: str) -> CacheResult:
        try:
            client = self._client()
            raw = await client.get(key) if client is not None else self._local_cache.get(key)
            if raw is None:
                log_event("optimization_cache_miss", namespace=namespace, key=key)
                return CacheResult(success=True, hit=False, key=key, namespace=namespace)  # type: ignore[arg-type]
            value = self._deserialize(raw)
            log_event("optimization_cache_hit", namespace=namespace, key=key)
            return CacheResult(success=True, hit=True, key=key, namespace=namespace, value=value)  # type: ignore[arg-type]
        except (RedisError, ValueError, TypeError) as exc:
            log_error("Optimization cache fetch failed", namespace=namespace, key=key, error_type=type(exc).__name__)
            if self.enable_in_memory_fallback and key in self._local_cache:
                return CacheResult(success=True, hit=True, key=key, namespace=namespace, value=self._local_cache[key])  # type: ignore[arg-type]
            raise CacheOperationError("cache fetch failed") from exc

    async def set(self, key: str, value: Any, *, namespace: str, ttl_seconds: int) -> CacheResult:
        try:
            payload = stable_json_dumps(value)
            client = self._client()
            if client is None:
                self._local_cache[key] = payload
            else:
                await client.set(key, payload, ex=ttl_seconds)
            log_event("optimization_cache_stored", namespace=namespace, key=key, ttl_seconds=ttl_seconds)
            return CacheResult(success=True, hit=False, key=key, namespace=namespace, value=value)  # type: ignore[arg-type]
        except RedisError as exc:
            log_error("Optimization cache store failed", namespace=namespace, key=key, error_type=type(exc).__name__)
            if self.enable_in_memory_fallback:
                self._local_cache[key] = value
                return CacheResult(success=True, key=key, namespace=namespace, value=value, metadata={"fallback": "memory"})  # type: ignore[arg-type]
            raise CacheOperationError("cache store failed") from exc

    def _deserialize(self, raw: Any) -> Any:
        if not isinstance(raw, str):
            return raw
        import json

        return json.loads(raw)

    def _delete_local(self, key_or_pattern: str) -> int:
        if "*" not in key_or_pattern:
            return int(self._local_cache.pop(key_or_pattern, None) is not None)
        prefix = key_or_pattern.rstrip("*")
        keys = [key for key in self._local_cache if key.startswith(prefix)]
        for key in keys:
            self._local_cache.pop(key, None)
        return len(keys)

