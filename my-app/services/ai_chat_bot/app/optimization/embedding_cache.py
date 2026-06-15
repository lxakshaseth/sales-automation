from app.models.cache_models import CacheResult
from app.optimization.cache_manager import CacheManager


class EmbeddingCacheManager:
    """Embedding cache to avoid repeated vector generation."""

    def __init__(self, *, cache_manager: CacheManager | None = None, ttl_seconds: int = 24 * 60 * 60) -> None:
        self.cache_manager = cache_manager or CacheManager()
        self.ttl_seconds = ttl_seconds

    async def get(self, text: str, *, model_name: str | None = None) -> CacheResult:
        return await self.cache_manager.fetch_cached_embedding(text, model_name=model_name)

    async def set(self, text: str, embedding: list[float], *, model_name: str | None = None) -> CacheResult:
        return await self.cache_manager.cache_embedding(
            text,
            embedding,
            model_name=model_name,
            ttl_seconds=self.ttl_seconds,
        )

