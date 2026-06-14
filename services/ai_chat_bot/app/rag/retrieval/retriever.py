from app.core.logger import log_event
from app.rag.models.retrieval_models import RetrievalConfig
from app.rag.models.search_models import SimilarityResult
from app.rag.retrieval.semantic_search_engine import SemanticSearchEngine


class Retriever:
    """Top-k semantic retriever over R4 vector indexes."""

    def __init__(self, *, semantic_engine: SemanticSearchEngine | None = None) -> None:
        self.semantic_engine = semantic_engine or SemanticSearchEngine()

    async def retrieve(self, query: str, config: RetrievalConfig | None = None, metadata_filter: dict | None = None) -> SimilarityResult:
        resolved_config = config or RetrievalConfig()
        return await self.retrieve_top_k(query, resolved_config, metadata_filter or {})

    async def retrieve_top_k(self, query: str, config: RetrievalConfig, metadata_filter: dict) -> SimilarityResult:
        log_event("rag_retriever_started", top_k=config.top_k, candidate_k=config.candidate_k)
        return await self.retrieve_by_similarity(query, config, metadata_filter)

    async def retrieve_by_vector(self, query_vector: list[float], config: RetrievalConfig, metadata_filter: dict) -> SimilarityResult:
        from app.rag.models.search_models import SearchQuery

        return await self.semantic_engine.vector_search_service.search(
            SearchQuery(query_vector=query_vector, top_k=config.candidate_k, metadata_filter=metadata_filter)
        )

    async def retrieve_by_similarity(self, query: str, config: RetrievalConfig, metadata_filter: dict) -> SimilarityResult:
        return await self.semantic_engine.search(
            query=query,
            top_k=config.candidate_k,
            metadata_filter=metadata_filter,
            embedding_config=config.embedding_config,
        )
