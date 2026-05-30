from typing import Any

from app.core.logger import log_error, log_event
from app.intelligence.confidence.exceptions import ConfidenceCalculationError, ConfidenceInputError
from app.intelligence.confidence.models import ConfidenceInput, ConfidenceMetrics, ConfidenceReason, ConfidenceResult
from app.intelligence.confidence.response_confidence import calculate_response_confidence
from app.intelligence.confidence.retrieval_confidence import calculate_retrieval_confidence
from app.intelligence.confidence.scoring_service import DEFAULT_CONFIDENCE_WEIGHTS, confidence_bucket, normalize_score, weighted_score
from app.intelligence.confidence.tool_confidence import calculate_tool_confidence


class ConfidenceEngine:
    """Single source of truth for AI confidence decisions."""

    def __init__(self, weights: dict[str, float] | None = None) -> None:
        self.weights = weights or DEFAULT_CONFIDENCE_WEIGHTS

    async def calculate_confidence(self, confidence_input: ConfidenceInput | dict[str, Any]) -> ConfidenceResult:
        log_event("confidence_calculation_started")
        try:
            resolved_input = confidence_input if isinstance(confidence_input, ConfidenceInput) else ConfidenceInput(**confidence_input)

            retrieval = await calculate_retrieval_confidence(
                retrieval_score=resolved_input.retrieval_score,
                rerank_score=resolved_input.rerank_score,
                chunk_relevance=resolved_input.chunk_relevance,
                chunk_scores=resolved_input.chunk_scores,
                chunk_count=resolved_input.chunk_count,
                retrieval_threshold=resolved_input.retrieval_threshold,
            )
            tool = await calculate_tool_confidence(
                tool_output=resolved_input.tool_output,
                tool_exists=resolved_input.tool_exists,
                parameters_validated=resolved_input.parameters_validated,
            )
            response = await calculate_response_confidence(
                response=resolved_input.llm_response,
                structured_output_valid=resolved_input.structured_output_valid,
                schema_validation_success=resolved_input.schema_validation_success,
                response_complete=resolved_input.response_complete,
                unsupported_claims=resolved_input.unsupported_claims,
            )

            metrics = ConfidenceMetrics(
                retrieval_confidence=retrieval.confidence,
                tool_confidence=tool.confidence,
                intent_confidence=normalize_score(resolved_input.intent_confidence),
                response_confidence=response.confidence,
                weights=self.weights,
            )
            overall_confidence = self.calculate_overall_confidence(metrics)
            confidence_level = self.evaluate_confidence_level(overall_confidence)

            reasoning_details = [*retrieval.reasons, *tool.reasons, *response.reasons]
            if metrics.intent_confidence >= 0.80:
                reasoning_details.append(ConfidenceReason(code="valid_intent", message="Intent confidence is high.", weight=0.15, source="intent"))
            elif metrics.intent_confidence < 0.60:
                reasoning_details.append(ConfidenceReason(code="weak_intent", message="Intent confidence is below execution threshold.", weight=0.15, source="intent"))

            recommendation = self.fallback_recommendation(overall_confidence)
            if recommendation:
                log_event("confidence_fallback_recommended", confidence=overall_confidence, action=recommendation["action"])
            if overall_confidence < 0.60:
                log_error("Low confidence warning", confidence=overall_confidence, confidence_level=confidence_level.value)

            result = ConfidenceResult(
                confidence=overall_confidence,
                confidence_level=confidence_level,
                reason=self.generate_reason(reasoning_details),
                recommendation=recommendation,
                indicators={
                    "retrieval_supported": retrieval.retrieval_supported,
                    "tool_verified": tool.tool_verified,
                    "schema_valid": response.schema_valid,
                    "hallucination_risk": response.hallucination_risk,
                },
                metrics=metrics,
                reasoning_details=reasoning_details,
                fallback_required=overall_confidence < 0.60,
                metadata=resolved_input.metadata,
            )
            log_event("final_confidence_score", confidence=result.confidence, confidence_level=result.confidence_level.value, fallback_required=result.fallback_required)
            return result
        except (ConfidenceInputError, ValueError):
            log_error("Invalid confidence calculation input", exc_info=True)
            return self.production_safe_fallback("invalid_confidence_input")
        except Exception as exc:
            log_error("Confidence calculation failed", exc_info=True, error_type=type(exc).__name__)
            if isinstance(exc, ConfidenceCalculationError):
                return self.production_safe_fallback("confidence_calculation_failed")
            raise

    def calculate_overall_confidence(self, metrics: ConfidenceMetrics) -> float:
        return weighted_score(
            {
                "retrieval_confidence": metrics.retrieval_confidence,
                "tool_confidence": metrics.tool_confidence,
                "intent_confidence": metrics.intent_confidence,
                "response_confidence": metrics.response_confidence,
            },
            weights=metrics.weights,
        )

    def generate_reason(self, reasons: list[ConfidenceReason]) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []
        for reason in sorted(reasons, key=lambda item: item.weight, reverse=True):
            if reason.code not in seen:
                ordered.append(reason.code)
                seen.add(reason.code)
        return ordered

    def evaluate_confidence_level(self, confidence: float) -> Any:
        return confidence_bucket(confidence)

    def fallback_recommendation(self, confidence: float) -> dict[str, str]:
        score = normalize_score(confidence)
        if score < 0.40:
            return {"action": "fallback_response"}
        if score < 0.60:
            return {"action": "request_clarification"}
        return {}

    def production_safe_fallback(self, reason_code: str) -> ConfidenceResult:
        metrics = ConfidenceMetrics(weights=self.weights)
        return ConfidenceResult(
            confidence=0.0,
            confidence_level=confidence_bucket(0.0),
            reason=[reason_code],
            recommendation={"action": "fallback_response"},
            indicators={
                "retrieval_supported": False,
                "tool_verified": False,
                "schema_valid": False,
                "hallucination_risk": True,
            },
            metrics=metrics,
            reasoning_details=[
                ConfidenceReason(
                    code=reason_code,
                    message="Confidence system returned a production-safe fallback.",
                    weight=1.0,
                    source="overall",
                )
            ],
            fallback_required=True,
        )


async def calculate_confidence(confidence_input: ConfidenceInput | dict[str, Any]) -> ConfidenceResult:
    return await ConfidenceEngine().calculate_confidence(confidence_input)
