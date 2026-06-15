from app.rag.models.search_models import SearchQuery, SimilarityResult
from app.rag.models.vector_models import VectorIndexConfig
from app.rag.vector_db.faiss_store import FAISSVectorStore
from app.rag.vector_db.search_engine import SearchEngine


class VectorSearchService:
    """Internal vector-only search service for future retrieval orchestration."""

    def __init__(self, *, store: FAISSVectorStore | None = None, config: VectorIndexConfig | None = None) -> None:
        self.store = store or FAISSVectorStore(config=config)
        self.search_engine = SearchEngine(store=self.store)

    async def search(self, query: SearchQuery) -> SimilarityResult:
        return await self.search_engine.similarity_search(query)
