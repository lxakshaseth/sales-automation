from typing import Any

from app.core.logger import log_error, log_event
from app.intelligence.confidence.exceptions import ConfidenceCalculationError
from app.intelligence.confidence.models import ConfidenceReason, ResponseConfidence
from app.intelligence.confidence.scoring_service import confidence_bucket

UNCERTAINTY_MARKERS = (
    "i think",
    "maybe",
    "possibly",
    "not sure",
    "i am not sure",
    "cannot verify",
    "could be",
)


def detect_uncertainty(response: str | dict[str, Any] | None) -> bool:
    text = str(response or "").lower()
    return any(marker in text for marker in UNCERTAINTY_MARKERS)


def detect_hallucination_risk(
    response: str | dict[str, Any] | None,
    unsupported_claims: list[str] | None = None,
    schema_validation_success: bool = False,
) -> bool:
    if unsupported_claims:
        return True
    if response is None:
        return True
    return not schema_validation_success and detect_uncertainty(response)


def evaluate_response_quality(response: str | dict[str, Any] | None, response_complete: bool | None = None) -> bool:
    if response_complete is not None:
        return response_complete
    if response is None:
        return False
    if isinstance(response, dict):
        return bool(response)
    return len(response.strip()) >= 5


async def calculate_response_confidence(
    response: str | dict[str, Any] | None = None,
    structured_output_valid: bool = False,
    schema_validation_success: bool = False,
    response_complete: bool | None = None,
    unsupported_claims: list[str] | None = None,
) -> ResponseConfidence:
    log_event("response_confidence_started")
    try:
        complete = evaluate_response_quality(response, response_complete=response_complete)
        uncertainty = detect_uncertainty(response)
        hallucination_risk = detect_hallucination_risk(
            response,
            unsupported_claims=unsupported_claims,
            schema_validation_success=schema_validation_success,
        )
        unsupported = bool(unsupported_claims)

        confidence = round(
            (1.0 if structured_output_valid else 0.0) * 0.25
            + (1.0 if schema_validation_success else 0.0) * 0.30
            + (1.0 if complete else 0.0) * 0.20
            + (0.0 if uncertainty else 1.0) * 0.10
            + (0.0 if hallucination_risk else 1.0) * 0.15,
            4,
        )

        reasons: list[ConfidenceReason] = []
        if schema_validation_success:
            reasons.append(ConfidenceReason(code="schema_valid", message="Response passed schema validation.", weight=0.30, source="response"))
        else:
            reasons.append(ConfidenceReason(code="schema_invalid", message="Response did not pass schema validation.", weight=0.30, source="response"))
        if complete:
            reasons.append(ConfidenceReason(code="response_complete", message="Response contains usable content.", weight=0.20, source="response"))
        if uncertainty:
            reasons.append(ConfidenceReason(code="uncertainty_detected", message="Response contains uncertainty markers.", weight=0.10, source="response"))
        if unsupported:
            reasons.append(ConfidenceReason(code="unsupported_claims", message="Response contains unsupported claims.", weight=0.15, source="response"))

        result = ResponseConfidence(
            confidence=confidence,
            confidence_level=confidence_bucket(confidence),
            schema_valid=schema_validation_success,
            hallucination_risk=hallucination_risk,
            structured_output_valid=structured_output_valid,
            response_complete=complete,
            uncertainty_detected=uncertainty,
            unsupported_claims_detected=unsupported,
            reasons=reasons,
        )
        log_event("response_confidence_calculated", confidence=result.confidence, confidence_level=result.confidence_level.value, hallucination_risk=hallucination_risk)
        return result
    except Exception as exc:
        log_error("Response confidence calculation failed", exc_info=True, error_type=type(exc).__name__)
        raise ConfidenceCalculationError("response confidence calculation failed") from exc
