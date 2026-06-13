from app.core.logger import log_error, log_event
from app.exceptions.context_exceptions import ContextRankingError
from app.models.context_models import MemoryContext, RetrievalContext
from app.models.ranking_models import RankedContext, RankingResult, RankingWeights
from app.utils.context_helpers import context_fingerprint, lexical_overlap_score


class ContextRanker:
    """Score and rank RAG + memory items for hallucination-resistant prompts."""

    def __init__(self, weights: RankingWeights | None = None) -> None:
        self.weights = weights or RankingWeights()

    async def rank_context(
        self,
        *,
        user_query: str,
        retrieved_context: list[RetrievalContext],
        memory_context: list[MemoryContext],
    ) -> RankingResult:
        log_event("context_ranking_started", retrieval_count=len(retrieved_context), memory_count=len(memory_context))
        try:
            ranked: list[RankedContext] = []
            dropped_duplicates = 0
            dropped_low_score = 0
            seen: set[str] = set()

            for item in retrieved_context:
                fingerprint = context_fingerprint(item.content)
                if fingerprint in seen:
                    dropped_duplicates += 1
                    continue
                seen.add(fingerprint)
                ranked_item = self._rank_retrieval(user_query, item)
                if ranked_item.score < self.weights.min_score:
                    dropped_low_score += 1
                    continue
                ranked.append(ranked_item)

            for item in memory_context:
                fingerprint = context_fingerprint(item.content)
                if fingerprint in seen:
                    dropped_duplicates += 1
                    continue
                seen.add(fingerprint)
                ranked_item = self._rank_memory(user_query, item)
                if ranked_item.score < self.weights.min_score:
                    dropped_low_score += 1
                    continue
                ranked.append(ranked_item)

            ranked.sort(key=lambda item: item.score, reverse=True)
            for index, item in enumerate(ranked, start=1):
                item.rank = index

            log_event(
                "context_ranking_completed",
                ranked_count=len(ranked),
                dropped_duplicates=dropped_duplicates,
                dropped_low_score=dropped_low_score,
            )
            return RankingResult(
                ranked_context=ranked,
                dropped_duplicates=dropped_duplicates,
                dropped_low_score=dropped_low_score,
            )
        except Exception as exc:
            log_error("Context ranking failed", error_type=type(exc).__name__, exc_info=True)
            raise ContextRankingError("Failed to rank context") from exc

    def _rank_retrieval(self, query: str, item: RetrievalContext) -> RankedContext:
        overlap = lexical_overlap_score(query, item.content)
        density = min(1.0, len(item.content.strip()) / 1200)
        score = (
            overlap * self.weights.query_overlap
            + item.score * self.weights.source_score
            + 0.7 * self.weights.importance
            + 0.65 * self.weights.confidence
            + density * 0.05
        )
        return RankedContext(
            context_id=item.context_id,
            source="retrieval",
            content=item.content,
            score=min(1.0, max(0.0, score)),
            rank=item.rank or 1,
            token_count=item.token_count,
            signals={
                "query_overlap": overlap,
                "source_score": item.score,
                "importance": 0.7,
                "confidence": 0.65,
                "density": density,
            },
            metadata=item.metadata | {"chunk_id": item.chunk_id, "document_id": item.document_id, "source_name": item.source_name},
        )

    def _rank_memory(self, query: str, item: MemoryContext) -> RankedContext:
        overlap = lexical_overlap_score(query, item.content)
        score = (
            overlap * self.weights.query_overlap
            + item.importance * self.weights.importance
            + item.recency_score * self.weights.recency
            + item.confidence * self.weights.confidence
            + 0.1
        )
        return RankedContext(
            context_id=item.context_id,
            source=item.memory_type,
            content=item.content,
            score=min(1.0, max(0.0, score)),
            rank=1,
            token_count=item.token_count,
            signals={
                "query_overlap": overlap,
                "importance": item.importance,
                "recency": item.recency_score,
                "confidence": item.confidence,
            },
            metadata=item.metadata,
        )

