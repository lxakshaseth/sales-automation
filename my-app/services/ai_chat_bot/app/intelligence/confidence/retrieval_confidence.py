from app.core.logger import log_error, log_event
from app.intelligence.confidence.exceptions import ConfidenceCalculationError, ConfidenceInputError
from app.intelligence.confidence.models import ConfidenceReason, RetrievalConfidence
from app.intelligence.confidence.scoring_service import confidence_bucket, normalize_score


def evaluate_chunk_quality(chunk_scores: list[float] | None = None, chunk_count: int | None = None) -> dict[str, float | int]:
    scores = [normalize_score(score) for score in (chunk_scores or [])]
    resolved_count = chunk_count if chunk_count is not None else len(scores)
    if resolved_count < 0:
        raise ConfidenceInputError("chunk_count cannot be negative")

    top_similarity = max(scores, default=0.0)
    average_similarity = round(sum(scores) / len(scores), 4) if scores else 0.0

    return {
        "top_chunk_similarity": top_similarity,
        "average_chunk_similarity": average_similarity,
        "chunk_count": resolved_count,
    }


def evaluate_relevance(
    retrieval_score: float | None = None,
    rerank_score: float | None = None,
    chunk_relevance: float | None = None,
    retrieval_threshold: float = 0.65,
) -> tuple[float, list[ConfidenceReason], bool]:
    normalized_retrieval = normalize_score(retrieval_score)
    normalized_rerank = normalize_score(rerank_score, default=normalized_retrieval)
    normalized_relevance = normalize_score(chunk_relevance, default=normalized_retrieval)
    threshold = normalize_score(retrieval_threshold, default=0.65)

    reasons: list[ConfidenceReason] = []
    if normalized_retrieval >= 0.85:
        reasons.append(ConfidenceReason(code="high_retrieval_match", message="Top retrieval similarity is high.", weight=0.35, source="retrieval"))
    elif normalized_retrieval < 0.50:
        reasons.append(ConfidenceReason(code="low_retrieval_match", message="Top retrieval similarity is below acceptable range.", weight=0.35, source="retrieval"))

    if normalized_rerank >= threshold:
        reasons.append(ConfidenceReason(code="rerank_verified", message="Rerank score meets retrieval threshold.", weight=0.25, source="retrieval"))
    else:
        reasons.append(ConfidenceReason(code="rerank_below_threshold", message="Rerank score is below retrieval threshold.", weight=0.25, source="retrieval"))

    if normalized_relevance >= threshold:
        reasons.append(ConfidenceReason(code="relevant_chunks", message="Retrieved chunks meet relevance threshold.", weight=0.25, source="retrieval"))
    else:
        reasons.append(ConfidenceReason(code="weak_chunk_relevance", message="Retrieved chunks are weakly relevant.", weight=0.25, source="retrieval"))

    relevance_score = round((normalized_retrieval * 0.45) + (normalized_rerank * 0.30) + (normalized_relevance * 0.25), 4)
    return relevance_score, reasons, relevance_score >= threshold


async def calculate_retrieval_confidence(
    retrieval_score: float | None = None,
    rerank_score: float | None = None,
    chunk_relevance: float | None = None,
    chunk_scores: list[float] | None = None,
    chunk_count: int | None = None,
    retrieval_threshold: float = 0.65,
) -> RetrievalConfidence:
    log_event("retrieval_confidence_started", retrieval_threshold=retrieval_threshold)
    try:
        quality = evaluate_chunk_quality(chunk_scores=chunk_scores, chunk_count=chunk_count)
        top_similarity = normalize_score(retrieval_score, default=float(quality["top_chunk_similarity"]))
        average_similarity = float(quality["average_chunk_similarity"])
        count = int(quality["chunk_count"])

        relevance_score, reasons, retrieval_supported = evaluate_relevance(
            retrieval_score=top_similarity,
            rerank_score=rerank_score,
            chunk_relevance=chunk_relevance if chunk_relevance is not None else average_similarity,
            retrieval_threshold=retrieval_threshold,
        )
        chunk_count_factor = 1.0 if count > 0 else 0.0
        confidence = round((relevance_score * 0.85) + (chunk_count_factor * 0.15), 4)

        if count == 0:
            reasons.append(ConfidenceReason(code="missing_retrieval_results", message="No retrieval chunks were supplied.", weight=0.15, source="retrieval"))
            confidence = min(confidence, 0.35)
            retrieval_supported = False

        result = RetrievalConfidence(
            confidence=confidence,
            confidence_level=confidence_bucket(confidence),
            retrieval_supported=retrieval_supported,
            top_chunk_similarity=top_similarity,
            average_chunk_similarity=average_similarity,
            rerank_score=normalize_score(rerank_score, default=top_similarity),
            chunk_relevance=normalize_score(chunk_relevance, default=average_similarity),
            chunk_count=count,
            retrieval_threshold=normalize_score(retrieval_threshold, default=0.65),
            reasons=reasons,
        )
        log_event("retrieval_confidence_calculated", confidence=result.confidence, confidence_level=result.confidence_level.value, chunk_count=count)
        return result
    except ConfidenceInputError:
        log_error("Invalid retrieval confidence input", exc_info=True)
        raise
    except Exception as exc:
        log_error("Retrieval confidence calculation failed", exc_info=True, error_type=type(exc).__name__)
        raise ConfidenceCalculationError("retrieval confidence calculation failed") from exc
