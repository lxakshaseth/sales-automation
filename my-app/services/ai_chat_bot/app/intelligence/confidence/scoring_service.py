from app.intelligence.confidence.exceptions import ConfidenceInputError
from app.intelligence.confidence.models import ConfidenceLevel

DEFAULT_CONFIDENCE_WEIGHTS = {
    "retrieval_confidence": 0.40,
    "tool_confidence": 0.30,
    "intent_confidence": 0.15,
    "response_confidence": 0.15,
}


def normalize_score(value: float | int | None, default: float = 0.0) -> float:
    if value is None:
        return default

    try:
        score = float(value)
    except (TypeError, ValueError) as exc:
        raise ConfidenceInputError("confidence score must be numeric") from exc

    if score != score:
        raise ConfidenceInputError("confidence score cannot be NaN")

    return round(min(max(score, 0.0), 1.0), 4)


def confidence_bucket(score: float | int | None) -> ConfidenceLevel:
    normalized = normalize_score(score)
    if normalized >= 0.80:
        return ConfidenceLevel.HIGH
    if normalized >= 0.60:
        return ConfidenceLevel.MEDIUM
    if normalized >= 0.40:
        return ConfidenceLevel.LOW
    return ConfidenceLevel.VERY_LOW


def weighted_score(scores: dict[str, float | int | None], weights: dict[str, float] | None = None) -> float:
    resolved_weights = weights or DEFAULT_CONFIDENCE_WEIGHTS
    if not resolved_weights:
        raise ConfidenceInputError("confidence weights are required")

    total_weight = sum(float(weight) for weight in resolved_weights.values())
    if total_weight <= 0:
        raise ConfidenceInputError("confidence weights must sum above zero")

    weighted_total = 0.0
    for key, weight in resolved_weights.items():
        weighted_total += normalize_score(scores.get(key)) * float(weight)

    return round(weighted_total / total_weight, 4)
