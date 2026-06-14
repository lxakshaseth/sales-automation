from typing import Any


class RetrievalError(RuntimeError):
    """Base class for production-safe semantic retrieval failures."""

    error_code = "retrieval_error"
    safe_message = "Semantic retrieval failed."

    def __init__(self, message: str | None = None, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message or self.safe_message)
        self.details = details or {}

    def to_response(self) -> dict[str, Any]:
        return {
            "error_code": self.error_code,
            "message": self.safe_message,
            "details": self.details,
        }


class EmptyQueryError(RetrievalError):
    error_code = "empty_query"
    safe_message = "Search query cannot be empty."


class QueryEmbeddingError(RetrievalError):
    error_code = "query_embedding_error"
    safe_message = "Query embedding could not be generated."


class RetrievalSearchError(RetrievalError):
    error_code = "retrieval_search_error"
    safe_message = "Semantic search could not be completed."


class RerankingError(RetrievalError):
    error_code = "reranking_error"
    safe_message = "Retrieved chunks could not be reranked."


class LowRelevanceError(RetrievalError):
    error_code = "low_relevance"
    safe_message = "No sufficiently relevant context was found."
