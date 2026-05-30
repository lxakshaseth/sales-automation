import hashlib
import time
from typing import Any

from app.core.logger import log_error, log_event


class CacheOptimizer:
    """Prevents repeated token spending with cache-ready architecture."""

    def __init__(self, ttl_seconds: int = 300) -> None:
        self.ttl_seconds = ttl_seconds
        self._memory_cache: dict[str, tuple[float, Any]] = {}

    def build_cache_key(self, value: str, *, namespace: str = "prompt") -> str:
        digest = hashlib.sha256(str(value or "").strip().lower().encode("utf-8")).hexdigest()
        return f"{namespace}:{digest}"

    async def detect_repeated_query(self, query: str) -> bool:
        key = self.build_cache_key(query, namespace="query")
        hit = await self.get_cached_context(key) is not None
        log_event("repeated_query_detected", cache_hit=hit)
        return hit

    async def get_cached_context(self, cache_key: str) -> Any | None:
        try:
            cached = self._memory_cache.get(cache_key)
            if not cached:
                return None
            expires_at, value = cached
            if expires_at < time.time():
                self._memory_cache.pop(cache_key, None)
                return None
            log_event("optimization_cache_hit", cache_key=cache_key)
            return value
        except Exception as exc:
            log_error("Optimization cache read failed", exc_info=True, error_type=type(exc).__name__)
            return None

    async def cache_optimization(self, cache_key: str, value: Any) -> None:
        try:
            self._memory_cache[cache_key] = (time.time() + self.ttl_seconds, value)
            log_event("optimization_cached", cache_key=cache_key, ttl_seconds=self.ttl_seconds)
        except Exception as exc:
            log_error("Optimization cache write failed", exc_info=True, error_type=type(exc).__name__)

    async def cache_prompt(self, prompt: str, optimized_prompt: str) -> str:
        key = self.build_cache_key(prompt, namespace="prompt")
        await self.cache_optimization(key, optimized_prompt)
        return key
