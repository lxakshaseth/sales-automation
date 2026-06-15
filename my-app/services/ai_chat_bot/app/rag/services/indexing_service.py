from app.rag.models.vector_models import DenseVector, VectorIndexConfig
from app.rag.vector_db.index_manager import IndexManager


class IndexingService:
    """Batch indexing facade with future Celery worker integration points."""

    def __init__(self, *, index_manager: IndexManager | None = None, config: VectorIndexConfig | None = None) -> None:
        self.index_manager = index_manager or IndexManager(config=config)

    async def ensure_index(self) -> None:
        await self.index_manager.create_index()

    async def batch_index(self, dense_vectors: list[DenseVector]) -> None:
        await self.index_manager.rebuild_index(dense_vectors)

    async def validate_index(self) -> bool:
        return await self.index_manager.validate_index()
