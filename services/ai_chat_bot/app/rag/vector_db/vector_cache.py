import asyncio
from collections import OrderedDict

from app.rag.models.search_models import SimilarityResult
from app.rag.models.vector_models import StoredVector


class VectorCache:
    """In-memory hot cache with Redis-shaped placeholders for future R4 scaling."""

    def __init__(self, *, max_entries: int = 5_000) -> None:
        self.max_entries = max_entries
        self._vectors: OrderedDict[str, StoredVector] = OrderedDict()
        self._search_results: OrderedDict[str, SimilarityResult] = OrderedDict()
        self._lock = asyncio.Lock()

    async def get_vector(self, vector_id: str) -> StoredVector | None:
        async with self._lock:
            vector = self._vectors.get(vector_id)
            if vector is not None:
                self._vectors.move_to_end(vector_id)
            return vector

    async def set_vector(self, vector: StoredVector) -> None:
        async with self._lock:
            self._vectors[vector.vector_id] = vector
            self._vectors.move_to_end(vector.vector_id)
            while len(self._vectors) > self.max_entries:
                self._vectors.popitem(last=False)

    async def get_search_result(self, cache_key: str) -> SimilarityResult | None:
        async with self._lock:
            result = self._search_results.get(cache_key)
            if result is not None:
                self._search_results.move_to_end(cache_key)
            return result

    async def set_search_result(self, cache_key: str, result: SimilarityResult) -> None:
        async with self._lock:
            self._search_results[cache_key] = result
            self._search_results.move_to_end(cache_key)

    async def get_from_redis_placeholder(self, cache_key: str):
        return None
