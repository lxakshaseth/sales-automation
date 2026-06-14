from typing import Any

from app.rag.models.search_models import SearchResult
from app.rag.models.vector_models import StoredVector


def metadata_matches(stored_vector: StoredVector, metadata_filter: dict[str, Any]) -> bool:
    if not metadata_filter:
        return True

    searchable = {
        "vector_id": stored_vector.vector_id,
        "chunk_id": stored_vector.chunk_id,
        "document_id": stored_vector.document_id,
        "embedding_model": stored_vector.embedding_model,
        "source_filename": stored_vector.metadata.source_filename,
        **stored_vector.metadata.extra,
    }
    return all(searchable.get(key) == value for key, value in metadata_filter.items())


def apply_score_threshold(results: list[SearchResult], threshold: float | None) -> list[SearchResult]:
    if threshold is None:
        return results
    return [result for result in results if result.score >= threshold]
