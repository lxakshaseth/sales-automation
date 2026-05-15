import asyncio
import hashlib
from collections import OrderedDict

from app.rag.models.retrieval_models import RetrievalRequest, RetrievalResult


class RetrievalCache:
    """Small in-memory cache with Redis-compatible method boundaries."""

    def __init__(self, *, max_entries: int = 2_000) -> None:
        self.max_entries = max_entries
        self._cache: OrderedDict[str, RetrievalResult] = OrderedDict()
        self._lock = asyncio.Lock()

    def build_key(self, request: RetrievalRequest) -> str:
        payload = request.model_dump_json(exclude={"request_id"})
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    async def get(self, cache_key: str) -> RetrievalResult | None:
        async with self._lock:
            result = self._cache.get(cache_key)
            if result is not None:
                self._cache.move_to_end(cache_key)
            return result

    async def set(self, cache_key: str, result: RetrievalResult) -> None:
        async with self._lock:
            self._cache[cache_key] = result
            self._cache.move_to_end(cache_key)
            while len(self._cache) > self.max_entries:
                self._cache.popitem(last=False)

    async def get_from_redis_placeholder(self, cache_key: str) -> RetrievalResult | None:
        return None
