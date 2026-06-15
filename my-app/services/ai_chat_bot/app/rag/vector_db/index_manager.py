from app.core.logger import log_event
from app.rag.models.vector_models import DenseVector, VectorIndexConfig
from app.rag.vector_db.faiss_store import FAISSVectorStore


class IndexManager:
    """Index lifecycle manager with future distributed indexing hooks."""

    def __init__(self, *, store: FAISSVectorStore | None = None, config: VectorIndexConfig | None = None) -> None:
        self.store = store or FAISSVectorStore(config=config)

    async def create_index(self) -> None:
        await self.store.initialize()

    async def optimize_index(self) -> None:
        # IndexFlat is already exact-search optimized for local development.
        log_event("rag_vector_index_optimize_placeholder", index_name=self.store.config.index_name)

    async def rebuild_index(self, dense_vectors: list[DenseVector]) -> None:
        await self.store.rebuild(dense_vectors)
        log_event("rag_vector_index_rebuilt", index_name=self.store.config.index_name, vector_count=len(dense_vectors))

    async def validate_index(self) -> bool:
        await self.store.initialize()
        return self.store.size == len(self.store.id_to_row) == len(self.store.row_to_id)
