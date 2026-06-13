import time

from app.core.logger import log_error, log_event
from app.rag.exceptions.vector_db_exceptions import VectorDBError
from app.rag.models.vector_models import BatchVectorResult, DenseVector, StoredVector, VectorIndexConfig
from app.rag.vector_db.faiss_store import FAISSVectorStore


class VectorManager:
    """Orchestrate vector storage operations over a swappable store backend."""

    def __init__(self, *, store: FAISSVectorStore | None = None, config: VectorIndexConfig | None = None) -> None:
        self.store = store or FAISSVectorStore(config=config)

    async def add_embedding(self, dense_vector: DenseVector) -> StoredVector:
        stored = await self.store.add_vector(dense_vector)
        if self.store.config.auto_persist:
            await self.store.persist()
        return stored

    async def add_batch_embeddings(self, dense_vectors: list[DenseVector]) -> BatchVectorResult:
        started_at = time.perf_counter()
        try:
            stored = await self.store.add_vectors(dense_vectors)
            if self.store.config.auto_persist:
                await self.store.persist()
            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
            log_event("rag_vector_batch_stored", inserted_count=len(stored), duration_ms=duration_ms)
            return BatchVectorResult(success=True, stored_vectors=stored, inserted_count=len(stored), duration_ms=duration_ms)
        except VectorDBError as exc:
            log_error("RAG vector batch storage failed", error_code=exc.error_code)
            return BatchVectorResult(success=False, errors=[exc.to_response()], duration_ms=round((time.perf_counter() - started_at) * 1000, 2))

    async def remove_embedding(self, vector_id: str) -> None:
        await self.store.remove_vector(vector_id)

    async def get_vector_by_id(self, vector_id: str) -> StoredVector:
        return await self.store.get_vector_by_id(vector_id)

    async def persist_index(self) -> None:
        await self.store.persist()
