import asyncio
from collections import OrderedDict

from app.core.logger import log_event
from app.rag.models.vector_models import DenseVector


class EmbeddingCache:
    """
    Hash-based in-memory embedding cache.

    Redis is intentionally not implemented in R3. The public methods are shaped
    so a Redis-backed implementation can replace this class without changing the
    embedding service.
    """

    def __init__(self, *, max_entries: int = 10_000) -> None:
        self.max_entries = max_entries
        self._cache: OrderedDict[str, DenseVector] = OrderedDict()
        self._lock = asyncio.Lock()

    async def get(self, cache_key: str) -> DenseVector | None:
        async with self._lock:
            vector = self._cache.get(cache_key)
            if vector is None:
                return None

            self._cache.move_to_end(cache_key)
            log_event("rag_embedding_cache_hit", cache_key=cache_key[:12])
            return vector

    async def set(self, cache_key: str, vector: DenseVector) -> None:
        async with self._lock:
            self._cache[cache_key] = vector
            self._cache.move_to_end(cache_key)
            while len(self._cache) > self.max_entries:
                self._cache.popitem(last=False)

            log_event("rag_embedding_cache_stored", cache_key=cache_key[:12], vector_id=vector.vector_id)

    async def invalidate(self, cache_key: str) -> None:
        async with self._lock:
            self._cache.pop(cache_key, None)

    async def clear(self) -> None:
        async with self._lock:
            self._cache.clear()

    async def get_from_redis_placeholder(self, cache_key: str) -> DenseVector | None:
        """Future Redis cache hook."""

        return None

