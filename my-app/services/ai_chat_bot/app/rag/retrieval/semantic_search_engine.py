from app.core.logger import log_error, log_event
from app.rag.embeddings.embedding_manager import EmbeddingManager
from app.rag.exceptions.retrieval_exceptions import QueryEmbeddingError, RetrievalSearchError
from app.rag.models.document_models import DocumentChunk, DocumentMetadata
from app.rag.models.embedding_models import EmbeddingConfig
from app.rag.models.search_models import SearchQuery, SimilarityResult
from app.rag.services.vector_search_service import VectorSearchService
from app.rag.utils.query_helpers import normalize_query_text


class SemanticSearchEngine:
    """Generate query embeddings and run vector-only semantic search."""

    def __init__(
        self,
        *,
        embedding_manager: EmbeddingManager | None = None,
        vector_search_service: VectorSearchService | None = None,
    ) -> None:
        self.embedding_manager = embedding_manager or EmbeddingManager()
        self.vector_search_service = vector_search_service or VectorSearchService()

    async def search(
        self,
        *,
        query: str,
        top_k: int = 5,
        score_threshold: float | None = None,
        metadata_filter: dict | None = None,
        embedding_config: EmbeddingConfig | None = None,
    ) -> SimilarityResult:
        normalized_query = normalize_query_text(query)
        log_event("rag_query_embedding_started", query_length=len(normalized_query))
        query_vector = await self._embed_query(normalized_query, embedding_config or EmbeddingConfig())
        log_event("rag_query_embedding_completed", vector_dimension=len(query_vector))

        try:
            return await self.vector_search_service.search(
                SearchQuery(
                    query_vector=query_vector,
                    top_k=top_k,
                    score_threshold=score_threshold,
                    metadata_filter=metadata_filter or {},
                )
            )
        except Exception as exc:
            log_error("RAG semantic vector search failed", error_type=type(exc).__name__)
            raise RetrievalSearchError("semantic vector search failed", details={"error_type": type(exc).__name__}) from exc

    async def _embed_query(self, query: str, config: EmbeddingConfig) -> list[float]:
        metadata = DocumentMetadata(filename="query.txt", extension=".txt", document_type="txt", loader_type="query")
        query_chunk = DocumentChunk(
            chunk_id=f"query:{abs(hash(query))}",
            document_id="query",
            chunk_index=0,
            content=query,
            token_count=max(1, len(query.split())),
            character_count=len(query),
            strategy="semantic",
            document_metadata=metadata,
        )
        response = await self.embedding_manager.embed_chunk(query_chunk, config)
        if not response.success or response.vector is None:
            raise QueryEmbeddingError("query embedding failed", details=response.error or {})
        return response.vector.vector
