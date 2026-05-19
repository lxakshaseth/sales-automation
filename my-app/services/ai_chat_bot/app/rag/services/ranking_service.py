from app.rag.models.ranking_models import RankedChunk
from app.rag.models.search_models import SearchResult
from app.rag.retrieval.relevance_filter import RelevanceFilter
from app.rag.retrieval.reranker import LightweightReranker


class RankingService:
    """Service wrapper for reranking and relevance filtering."""

    def __init__(self, *, reranker: LightweightReranker | None = None, relevance_filter: RelevanceFilter | None = None) -> None:
        self.reranker = reranker or LightweightReranker()
        self.relevance_filter = relevance_filter or RelevanceFilter()

    async def rerank(self, query: str, results: list[SearchResult], *, similarity_weight: float = 0.75, keyword_weight: float = 0.25) -> list[RankedChunk]:
        return await self.reranker.rerank(
            query=query,
            results=results,
            similarity_weight=similarity_weight,
            keyword_weight=keyword_weight,
        )

    async def filter_relevant(self, chunks: list[RankedChunk], *, threshold: float = 0.65, top_k: int = 5) -> list[RankedChunk]:
        return await self.relevance_filter.filter(chunks, threshold=threshold, top_k=top_k)
