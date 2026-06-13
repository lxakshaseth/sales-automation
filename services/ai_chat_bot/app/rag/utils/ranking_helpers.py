from app.rag.models.search_models import SearchResult
from app.rag.utils.query_helpers import query_terms


def normalize_similarity_score(score: float) -> float:
    # FAISS cosine scores should already be -1..1; map to 0..1 for final ranking.
    return max(0.0, min(1.0, (float(score) + 1.0) / 2.0))


def keyword_overlap_score(query: str, candidate_text: str) -> float:
    terms = query_terms(query)
    if not terms:
        return 0.0
    candidate_terms = query_terms(candidate_text)
    if not candidate_terms:
        return 0.0
    return len(terms & candidate_terms) / len(terms)


def candidate_text_from_result(result: SearchResult) -> str:
    stored = result.stored_vector
    if stored is None:
        return ""
    extra = stored.metadata.extra or {}
    chunk_metadata = extra.get("chunk_metadata")
    text_candidates = [
        extra.get("content"),
        extra.get("text"),
        extra.get("chunk_content"),
        chunk_metadata.get("content") if isinstance(chunk_metadata, dict) else None,
        chunk_metadata.get("text") if isinstance(chunk_metadata, dict) else None,
    ]
    return next((str(value) for value in text_candidates if value), "")
