import time

from app.core.logger import log_error, log_event
from app.rag.exceptions.vector_db_exceptions import VectorDBError, VectorSearchError
from app.rag.models.search_models import SearchQuery, SearchResult, SimilarityResult
from app.rag.vector_db.faiss_store import FAISSVectorStore


class SearchEngine:
    """Similarity search engine over stored vectors only."""

    def __init__(self, *, store: FAISSVectorStore) -> None:
        self.store = store

    async def similarity_search(self, query: SearchQuery) -> SimilarityResult:
        started_at = time.perf_counter()
        log_event("rag_vector_search_started", top_k=query.top_k, score_threshold=query.score_threshold)

        try:
            results = await self.search_by_vector(query)
            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
            log_event("rag_vector_search_completed", returned_count=len(results), duration_ms=duration_ms)
            return SimilarityResult(success=True, results=results, query_top_k=query.top_k, returned_count=len(results), duration_ms=duration_ms)
        except VectorDBError as exc:
            log_error("RAG vector search failed", error_code=exc.error_code)
            return SimilarityResult(success=False, error=exc.to_response(), query_top_k=query.top_k, duration_ms=round((time.perf_counter() - started_at) * 1000, 2))

    async def search_by_vector(self, query: SearchQuery) -> list[SearchResult]:
        return self.filter_results(await self.store.search(query), query)

    async def search_by_text_placeholder(self, text: str, top_k: int = 5) -> SimilarityResult:
        raise VectorSearchError(
            "text search requires Layer R5 retrieval orchestration with query embeddings",
            details={"top_k": top_k, "text_length": len(text or "")},
        )

    def filter_results(self, results: list[SearchResult], query: SearchQuery) -> list[SearchResult]:
        if query.score_threshold is None:
            return results
        return [result for result in results if result.score >= query.score_threshold]
