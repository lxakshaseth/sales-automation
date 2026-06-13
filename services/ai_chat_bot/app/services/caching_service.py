from typing import Any

from app.models.cache_models import CacheResult
from app.optimization.cache_manager import CacheManager
from app.optimization.embedding_cache import EmbeddingCacheManager
from app.optimization.retrieval_cache import RetrievalCacheManager


class CachingService:
    """Service facade for R10 cache lifecycle operations."""

    def __init__(self, *, cache_manager: CacheManager | None = None) -> None:
        self.cache_manager = cache_manager or CacheManager()
        self.retrieval_cache = RetrievalCacheManager(cache_manager=self.cache_manager)
        self.embedding_cache = EmbeddingCacheManager(cache_manager=self.cache_manager)

    async def get_retrieval(self, query: str, *, metadata_filter: dict | None = None) -> CacheResult:
        return await self.retrieval_cache.get(query, metadata_filter=metadata_filter)

    async def set_retrieval(self, query: str, results: Any, *, metadata_filter: dict | None = None) -> CacheResult:
        return await self.retrieval_cache.set(query, results, metadata_filter=metadata_filter)

    async def get_embedding(self, text: str, *, model_name: str | None = None) -> CacheResult:
        return await self.embedding_cache.get(text, model_name=model_name)

    async def set_embedding(self, text: str, embedding: list[float], *, model_name: str | None = None) -> CacheResult:
        return await self.embedding_cache.set(text, embedding, model_name=model_name)

    async def invalidate(self, namespace: str, value: Any | None = None) -> CacheResult:
        return await self.cache_manager.invalidate_cache(namespace, value)

