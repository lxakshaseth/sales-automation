from app.rag.embeddings.embedding_service import EmbeddingService
from app.rag.models.document_models import DocumentChunk
from app.rag.models.embedding_models import BatchEmbeddingResult, EmbeddingConfig, EmbeddingResponse


class EmbeddingManager:
    """
    Facade for internal platform services.

    Future Celery tasks, ingestion workflows, or AI service hooks should depend
    on this manager instead of constructing lower-level embedding components.
    """

    def __init__(self, *, embedding_service: EmbeddingService | None = None) -> None:
        self.embedding_service = embedding_service or EmbeddingService()

    async def embed_chunk(self, chunk: DocumentChunk, config: EmbeddingConfig | None = None) -> EmbeddingResponse:
        return await self.embedding_service.generate_embedding(chunk, config)

    async def embed_chunks(self, chunks: list[DocumentChunk], config: EmbeddingConfig | None = None) -> BatchEmbeddingResult:
        return await self.embedding_service.generate_embeddings_batch(chunks, config)

