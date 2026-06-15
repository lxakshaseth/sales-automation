import time

from app.core.logger import log_error, log_event
from app.rag.exceptions.retrieval_exceptions import EmptyQueryError, LowRelevanceError, RetrievalError
from app.rag.models.retrieval_models import RetrievalRequest, RetrievalResult
from app.rag.retrieval.hybrid_search import HybridSearch
from app.rag.retrieval.query_expansion import QueryExpansion
from app.rag.retrieval.relevance_filter import RelevanceFilter
from app.rag.retrieval.reranker import LightweightReranker
from app.rag.retrieval.retrieval_cache import RetrievalCache
from app.rag.utils.query_helpers import normalize_query_text
from app.rag.utils.retrieval_helpers import cap_ranked_chunks, deduplicate_ranked_chunks


class RetrievalManager:
    """Coordinate R5 query expansion, semantic search, reranking, and filtering."""

    def __init__(
        self,
        *,
        query_expander: QueryExpansion | None = None,
        hybrid_search: HybridSearch | None = None,
        reranker: LightweightReranker | None = None,
        relevance_filter: RelevanceFilter | None = None,
        cache: RetrievalCache | None = None,
    ) -> None:
        self.query_expander = query_expander or QueryExpansion()
        self.hybrid_search = hybrid_search or HybridSearch()
        self.reranker = reranker or LightweightReranker()
        self.relevance_filter = relevance_filter or RelevanceFilter()
        self.cache = cache or RetrievalCache()

    async def retrieve(self, request: RetrievalRequest) -> RetrievalResult:
        started_at = time.perf_counter()
        normalized_query = normalize_query_text(request.query)
        if not normalized_query:
            error = EmptyQueryError()
            return RetrievalResult(success=False, query=request.query, error=error.to_response())

        cache_key = self.cache.build_key(request)
        if request.config.enable_cache:
            cached = await self.cache.get(cache_key)
            if cached is not None:
                log_event("rag_retrieval_cache_hit", request_id=request.request_id)
                return cached

        log_event("rag_retrieval_started", query_length=len(normalized_query), top_k=request.config.top_k)
        try:
            expanded_queries = await self.query_expander.expand(normalized_query, enabled=request.config.enable_query_expansion)
            candidate_results = []
            for expanded_query in expanded_queries:
                similarity_result = await self.hybrid_search.search(expanded_query, request.config, request.metadata_filter)
                if not similarity_result.success:
                    raise RetrievalError("semantic search failed", details=similarity_result.error or {})
                candidate_results.extend(similarity_result.results)

            ranked = await self.reranker.rerank(
                query=normalized_query,
                results=candidate_results,
                similarity_weight=request.config.similarity_weight,
                keyword_weight=request.config.keyword_weight,
            ) if request.config.enable_reranking else []

            ranked = deduplicate_ranked_chunks(ranked)
            filtered = await self.relevance_filter.filter(
                ranked,
                threshold=request.config.relevance_threshold,
                top_k=request.config.top_k,
            )
            final_chunks = cap_ranked_chunks(filtered, request.config.top_k)
            warnings: list[str] = []
            if not final_chunks:
                warnings.append(LowRelevanceError.safe_message)
                log_event("rag_retrieval_low_relevance", candidate_count=len(candidate_results), threshold=request.config.relevance_threshold)

            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
            result = RetrievalResult(
                success=True,
                query=normalized_query,
                expanded_queries=expanded_queries,
                chunks=final_chunks,
                warnings=warnings,
                returned_count=len(final_chunks),
                duration_ms=duration_ms,
            )
            if request.config.enable_cache:
                await self.cache.set(cache_key, result)
            log_event("rag_retrieval_completed", returned_count=len(final_chunks), duration_ms=duration_ms)
            return result
        except RetrievalError as exc:
            log_error("RAG retrieval failed", error_code=exc.error_code, request_id=request.request_id)
            return RetrievalResult(
                success=False,
                query=normalized_query,
                error=exc.to_response(),
                duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
            )
        except Exception as exc:
            log_error("Unexpected RAG retrieval failure", error_type=type(exc).__name__, request_id=request.request_id, exc_info=True)
            error = RetrievalError(details={"error_type": type(exc).__name__})
            return RetrievalResult(
                success=False,
                query=normalized_query,
                error=error.to_response(),
                duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
            )
