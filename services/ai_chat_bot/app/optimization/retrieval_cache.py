from typing import Any

from app.models.cache_models import CacheResult
from app.optimization.cache_manager import CacheManager
from app.utils.cache_helpers import normalize_query_for_cache


class RetrievalCacheManager:
    """Semantic retrieval cache with normalized multilingual query keys."""

    def __init__(self, *, cache_manager: CacheManager | None = None, ttl_seconds: int = 900) -> None:
        self.cache_manager = cache_manager or CacheManager()
        self.ttl_seconds = ttl_seconds

    async def get(self, query: str, *, metadata_filter: dict | None = None) -> CacheResult:
        return await self.cache_manager.fetch_cached_retrieval(
            normalize_query_for_cache(query),
            metadata=metadata_filter or {},
        )

    async def set(self, query: str, results: Any, *, metadata_filter: dict | None = None) -> CacheResult:
        return await self.cache_manager.cache_retrieval(
            normalize_query_for_cache(query),
            results,
            ttl_seconds=self.ttl_seconds,
            metadata=metadata_filter or {},
        )

