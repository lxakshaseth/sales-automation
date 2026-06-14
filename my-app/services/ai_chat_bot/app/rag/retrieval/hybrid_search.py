from app.core.logger import log_event
from app.rag.models.retrieval_models import RetrievalConfig
from app.rag.models.search_models import SimilarityResult
from app.rag.retrieval.retriever import Retriever


class HybridSearch:
    """Hybrid retrieval placeholder: semantic now, BM25/metadata weighting later."""

    def __init__(self, *, retriever: Retriever | None = None) -> None:
        self.retriever = retriever or Retriever()

    async def search(self, query: str, config: RetrievalConfig, metadata_filter: dict | None = None) -> SimilarityResult:
        log_event("rag_hybrid_search_placeholder", mode=config.retrieval_mode)
        return await self.retriever.retrieve(query, config, metadata_filter or {})
