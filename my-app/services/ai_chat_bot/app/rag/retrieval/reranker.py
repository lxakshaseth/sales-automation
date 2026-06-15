from app.core.logger import log_event
from app.rag.exceptions.retrieval_exceptions import RerankingError
from app.rag.models.ranking_models import RankedChunk
from app.rag.models.search_models import SearchResult
from app.rag.utils.ranking_helpers import candidate_text_from_result, keyword_overlap_score, normalize_similarity_score


class LightweightReranker:
    """Fast score-adjustment reranker with future cross-encoder swap point."""

    async def rerank(
        self,
        *,
        query: str,
        results: list[SearchResult],
        similarity_weight: float = 0.75,
        keyword_weight: float = 0.25,
    ) -> list[RankedChunk]:
        try:
            ranked: list[RankedChunk] = []
            for result in results:
                stored = result.stored_vector
                if stored is None:
                    continue

                candidate_text = candidate_text_from_result(result)
                semantic_score = normalize_similarity_score(result.score)
                lexical_score = keyword_overlap_score(query, candidate_text)
                final_score = max(0.0, min(1.0, semantic_score * similarity_weight + lexical_score * keyword_weight))

                ranked.append(
                    RankedChunk(
                        chunk_id=result.chunk_id,
                        document_id=result.document_id,
                        vector_id=result.vector_id,
                        rank=result.rank,
                        similarity_score=result.score,
                        rerank_score=final_score,
                        final_score=final_score,
                        source_filename=stored.metadata.source_filename,
                        content=candidate_text or None,
                        chunk_metadata=stored.metadata.extra,
                        retrieval_metadata={
                            "semantic_score_normalized": semantic_score,
                            "keyword_overlap_score": lexical_score,
                            "vector_rank": result.rank,
                            "distance": result.distance,
                        },
                    )
                )

            ranked.sort(key=lambda item: item.final_score, reverse=True)
            reranked = [item.model_copy(update={"rank": index + 1}) for index, item in enumerate(ranked)]
            log_event("rag_reranking_completed", candidate_count=len(results), reranked_count=len(reranked))
            return reranked
        except Exception as exc:
            raise RerankingError("lightweight reranking failed", details={"error_type": type(exc).__name__}) from exc
