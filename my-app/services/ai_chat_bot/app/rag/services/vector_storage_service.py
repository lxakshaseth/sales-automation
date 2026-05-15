from app.rag.models.vector_models import BatchVectorResult, DenseVector, StoredVector, VectorIndexConfig
from app.rag.vector_db.vector_manager import VectorManager


class VectorStorageService:
    """Internal service for storing R3 dense vectors in the R4 vector database."""

    def __init__(self, *, manager: VectorManager | None = None, config: VectorIndexConfig | None = None) -> None:
        self.manager = manager or VectorManager(config=config)

    async def store_vector(self, dense_vector: DenseVector) -> StoredVector:
        return await self.manager.add_embedding(dense_vector)

    async def store_vectors(self, dense_vectors: list[DenseVector]) -> BatchVectorResult:
        return await self.manager.add_batch_embeddings(dense_vectors)

    async def persist(self) -> None:
        await self.manager.persist_index()
