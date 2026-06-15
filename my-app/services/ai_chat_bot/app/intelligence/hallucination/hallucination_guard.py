import logging
from typing import Any

from app.core.logger import log_error, log_event
from app.intelligence.hallucination.models import (
    FallbackResponse,
    HallucinationReport,
    RiskAssessment,
    RiskLevel,
    ValidationAction,
    ValidationInput,
    ValidationResult,
)
from app.intelligence.hallucination.validation_pipeline import ValidationPipeline

logger = logging.getLogger(__name__)


class HallucinationGuard:
    """Final safety gate before an AI response reaches the user."""

    FALLBACKS = (
        "I could not verify this information.",
        "The available data is insufficient to provide a reliable answer.",
        "I need additional information before I can answer confidently.",
    )

    def __init__(self, pipeline: ValidationPipeline | None = None) -> None:
        self.pipeline = pipeline or ValidationPipeline()

    async def validate_response(self, validation_input: ValidationInput | dict[str, Any]) -> ValidationResult:
        try:
            data = validation_input if isinstance(validation_input, ValidationInput) else ValidationInput(**validation_input)
            log_event("hallucination_check_started", confidence=self._confidence(data))
            report = await self.pipeline.run_validation_pipeline(data)
            fallback = None
            response = data.response
            if not report.valid:
                fallback = self.generate_safe_fallback(report)
                response = fallback.response
                logger.warning(
                    "fallback_triggered",
                    extra={
                        "layer": "hallucination",
                        "reason": fallback.reason,
                        "score": report.risk.risk_score,
                        "hallucination_score": report.risk.risk_score,
                        "validation_result": report.valid,
                        "fallback_reason": fallback.reason,
                        "user_input": data.response[:500],
                        "tenant_id": data.metadata.get("tenant_id", ""),
                    },
                )
                log_event(
                    "FALLBACK_TRIGGER_REASON",
                    layer="hallucination",
                    reason=fallback.reason,
                    risk_score=report.risk.risk_score,
                    risk_level=report.risk.risk_level.value,
                )
                log_event("hallucination_fallback_activated", action=fallback.action.value, reason=fallback.reason)
            result = ValidationResult(
                valid=report.valid,
                action=report.action,
                response=response,
                original_response=data.response,
                report=report,
                fallback=fallback,
                metadata=data.metadata,
            )
            log_event("hallucination_check_completed", valid=result.valid, action=result.action.value, risk_level=report.risk.risk_level.value)
            return result
        except Exception as exc:
            logger.exception("hallucination_guard_failure")
            log_error("Hallucination guard failed; returning production-safe fallback", exc_info=True, error_type=type(exc).__name__)
            report = self.build_validation_report(
                risk=RiskAssessment(risk_level=RiskLevel.CRITICAL_RISK, risk_score=1.0, factors=["hallucination_guard_failure"]),
                confidence=0.0,
                reasons=["hallucination_guard_failure"],
            )
            fallback = FallbackResponse(response=self.FALLBACKS[0], reason="hallucination_guard_failure")
            return ValidationResult(valid=False, action=ValidationAction.REJECT, response=fallback.response, original_response="", report=report, fallback=fallback)

    def evaluate_hallucination_risk(self, report: HallucinationReport) -> RiskAssessment:
        return report.risk

    def enforce_confidence_threshold(self, confidence: float) -> ValidationAction:
        if confidence < 0.40:
            log_event("confidence_threshold_rejected", confidence=confidence)
            return ValidationAction.REJECT
        if confidence < 0.60:
            log_event("confidence_threshold_warning", confidence=confidence)
            return ValidationAction.WARNING
        return ValidationAction.ALLOW

    def generate_safe_fallback(self, report: HallucinationReport) -> FallbackResponse:
        if report.action == ValidationAction.WARNING:
            return FallbackResponse(action=ValidationAction.WARNING, response=self.FALLBACKS[2], reason="clarification_required")
        if "tool_verification_failure" in report.risk.factors or any("tool" in reason for reason in report.reasons):
            return FallbackResponse(action=ValidationAction.REJECT, response=self.FALLBACKS[0], reason="tool_result_not_verified")
        if "low_source_coverage" in report.risk.factors or "unsupported_claims" in report.risk.factors:
            return FallbackResponse(action=ValidationAction.REJECT, response=self.FALLBACKS[1], reason="insufficient_verified_evidence")
        return FallbackResponse(action=ValidationAction.REJECT, response=self.FALLBACKS[0], reason="hallucination_risk_detected")

    def build_validation_report(self, *, risk: RiskAssessment, confidence: float, reasons: list[str]) -> HallucinationReport:
        from app.intelligence.hallucination.models import FactCheckResult, GroundingResult, SourceVerification

        return HallucinationReport(
            valid=False,
            risk=risk,
            source_verification=SourceVerification(verified=False),
            grounding=GroundingResult(grounded=False),
            fact_check=FactCheckResult(passed=False),
            confidence=confidence,
            action=ValidationAction.REJECT,
            reasons=reasons,
        )

    def _confidence(self, data: ValidationInput) -> float:
        if data.confidence_result and isinstance(data.confidence_result.get("confidence"), int | float):
            return float(data.confidence_result["confidence"])
        return data.confidence


async def validate_response(validation_input: ValidationInput | dict[str, Any]) -> ValidationResult:
    return await HallucinationGuard().validate_response(validation_input)
