from typing import Any

from app.core.logger import log_error, log_event
from app.intelligence.hallucination.fact_checker import FactChecker
from app.intelligence.hallucination.models import (
    FactCheckResult,
    GroundingResult,
    HallucinationReport,
    RiskAssessment,
    RiskLevel,
    SourceVerification,
    ValidationAction,
    ValidationInput,
    ValidationResult,
)
from app.intelligence.hallucination.response_grounding import ResponseGrounder
from app.intelligence.hallucination.source_verifier import SourceVerifier


class ValidationPipeline:
    """Central hallucination verification workflow."""

    def __init__(
        self,
        source_verifier: SourceVerifier | None = None,
        grounder: ResponseGrounder | None = None,
        fact_checker: FactChecker | None = None,
    ) -> None:
        self.source_verifier = source_verifier or SourceVerifier()
        self.grounder = grounder or ResponseGrounder()
        self.fact_checker = fact_checker or FactChecker(self.source_verifier)

    async def run_validation_pipeline(self, validation_input: ValidationInput | dict[str, Any]) -> HallucinationReport:
        try:
            data = validation_input if isinstance(validation_input, ValidationInput) else ValidationInput(**validation_input)
            confidence = self._resolve_confidence(data)
            if not self._strict_validation_required(data):
                log_event(
                    "FACT_CHECK_SKIPPED",
                    reason="conversational_response",
                    request_type=data.metadata.get("request_type"),
                    retrieved_count=len(data.retrieved_chunks),
                )
                log_event(
                    "HALLUCINATION_SKIPPED",
                    reason="conversational_response",
                    request_type=data.metadata.get("request_type"),
                    retrieved_count=len(data.retrieved_chunks),
                )
                report = self._skipped_report(confidence=confidence)
                log_event("hallucination_validation_result", valid=report.valid, action=report.action.value, risk_level=report.risk.risk_level.value)
                return report

            sources = [*data.retrieved_chunks, *data.tool_outputs, *data.memory_context, *data.system_context]
            source_verification = self.source_verifier.verify_sources(
                data.response,
                retrieved_chunks=data.retrieved_chunks,
                tool_outputs=data.tool_outputs,
                memory_context=data.memory_context,
                system_context=data.system_context,
            )
            grounding = self.grounder.ground_response(
                data.response,
                retrieved_chunks=data.retrieved_chunks,
                tool_outputs=data.tool_outputs,
                memory_context=data.memory_context,
            )
            fact_check = self.fact_checker.check_facts(data.response, sources)
            risk = self._assess_risk(
                source_coverage=source_verification.coverage,
                confidence=confidence,
                unsupported_claim_count=len(set(source_verification.unsupported_claims + fact_check.unsupported_claims)),
                tool_failure_count=len(grounding.tool_failures),
                grounded=grounding.grounded,
            )
            action = self._action_for(risk, confidence)
            valid = action == ValidationAction.ALLOW and source_verification.verified and grounding.grounded and fact_check.passed
            reasons = self._reasons(source_verification, grounding, fact_check, risk, confidence)
            report = HallucinationReport(
                valid=valid,
                risk=risk,
                source_verification=source_verification,
                grounding=grounding,
                fact_check=fact_check,
                confidence=confidence,
                action=action if valid else self._blocked_action(action, confidence, risk),
                reasons=reasons,
            )
            log_event("hallucination_validation_result", valid=report.valid, action=report.action.value, risk_level=report.risk.risk_level.value)
            return report
        except Exception as exc:
            log_error("Validation pipeline failed", exc_info=True, error_type=type(exc).__name__)
            return self._failed_report(str(exc))

    async def verify_response(self, validation_input: ValidationInput | dict[str, Any]) -> HallucinationReport:
        return await self.run_validation_pipeline(validation_input)

    def generate_validation_result(self, original_response: str, report: HallucinationReport, fallback_response: str | None = None) -> ValidationResult:
        response = original_response if report.valid else fallback_response or "I could not verify this information."
        return ValidationResult(
            valid=report.valid,
            action=report.action,
            response=response,
            original_response=original_response,
            report=report,
        )

    def _resolve_confidence(self, data: ValidationInput) -> float:
        if data.confidence_result and isinstance(data.confidence_result.get("confidence"), int | float):
            return max(0.0, min(1.0, float(data.confidence_result["confidence"])))
        return data.confidence

    def _assess_risk(
        self,
        *,
        source_coverage: float,
        confidence: float,
        unsupported_claim_count: int,
        tool_failure_count: int,
        grounded: bool,
    ) -> RiskAssessment:
        risk_score = 0.0
        factors: list[str] = []
        if source_coverage < 0.40:
            risk_score += 0.35
            factors.append("low_source_coverage")
        elif source_coverage < 0.70:
            risk_score += 0.20
            factors.append("partial_source_coverage")
        if confidence < 0.40:
            risk_score += 0.55
            factors.append("very_low_confidence")
        elif confidence < 0.60:
            risk_score += 0.20
            factors.append("low_confidence")
        elif confidence < 0.80:
            risk_score += 0.10
            factors.append("medium_confidence")
        if unsupported_claim_count:
            risk_score += min(0.35, unsupported_claim_count * 0.12)
            factors.append("unsupported_claims")
        if tool_failure_count:
            risk_score += 0.40
            factors.append("tool_verification_failure")
        if not grounded:
            risk_score += 0.20
            factors.append("ungrounded_response")
        risk_score = round(min(1.0, risk_score), 4)
        if risk_score >= 0.80:
            level = RiskLevel.CRITICAL_RISK
        elif risk_score >= 0.55:
            level = RiskLevel.HIGH_RISK
        elif risk_score >= 0.30:
            level = RiskLevel.MEDIUM_RISK
        else:
            level = RiskLevel.LOW_RISK
        return RiskAssessment(risk_level=level, risk_score=risk_score, factors=factors, source_coverage=source_coverage, confidence=confidence)

    def _action_for(self, risk: RiskAssessment, confidence: float) -> ValidationAction:
        if confidence < 0.40 or risk.risk_level in {RiskLevel.HIGH_RISK, RiskLevel.CRITICAL_RISK}:
            return ValidationAction.REJECT
        if confidence < 0.60 or risk.risk_level == RiskLevel.MEDIUM_RISK:
            return ValidationAction.WARNING
        return ValidationAction.ALLOW

    def _blocked_action(self, action: ValidationAction, confidence: float, risk: RiskAssessment) -> ValidationAction:
        if confidence < 0.40 or risk.risk_level in {RiskLevel.HIGH_RISK, RiskLevel.CRITICAL_RISK}:
            return ValidationAction.REJECT
        return ValidationAction.WARNING

    def _reasons(self, source_verification, grounding, fact_check, risk, confidence: float) -> list[str]:
        reasons = list(risk.factors)
        if not source_verification.verified:
            reasons.append("source_verification_failed")
        if grounding.tool_failures:
            reasons.extend(grounding.tool_failures)
        if not fact_check.passed:
            reasons.append("fact_check_failed")
        if confidence < 0.60:
            reasons.append("confidence_threshold_violation")
        return sorted(set(reasons))

    def _strict_validation_required(self, data: ValidationInput) -> bool:
        metadata = data.metadata or {}
        request_type = str(metadata.get("request_type") or "").lower()
        reasoning_mode = str(metadata.get("reasoning_mode") or "").lower()
        conversational_types = {"", "chat", "greeting", "small_talk", "conversation", "casual_chat"}
        conversational_modes = {"", "simple_reply"}

        if metadata.get("tool_required") is True or metadata.get("use_rag") is True:
            return True
        if data.retrieved_chunks or data.tool_outputs:
            return True
        if request_type not in conversational_types or reasoning_mode not in conversational_modes:
            return True
        return self._has_strict_factual_claims(data.response)

    def _has_strict_factual_claims(self, response: str) -> bool:
        lower = response.lower()
        high_risk_markers = (
            *self.fact_checker.HALLUCINATION_MARKERS,
            "according to",
            "database",
            "record shows",
            "guaranteed",
            "price is",
            "costs $",
            "costs ₹",
            "today's date",
            "current time",
        )
        return any(marker in lower for marker in high_risk_markers)

    def _skipped_report(self, *, confidence: float) -> HallucinationReport:
        return HallucinationReport(
            valid=True,
            risk=RiskAssessment(risk_level=RiskLevel.LOW_RISK, risk_score=0.0, factors=["conversational_validation_skipped"], source_coverage=1.0, confidence=confidence),
            source_verification=SourceVerification(verified=True, coverage=1.0, matched_claims=[], unsupported_claims=[], evidence_sources=[], missing_sources=[]),
            grounding=GroundingResult(grounded=True, retrieval_grounded=False, tool_grounded=False, memory_grounded=False),
            fact_check=FactCheckResult(passed=True, factual_consistency=1.0, verified_claims=[], unsupported_claims=[], hallucination_indicators=[]),
            confidence=confidence,
            action=ValidationAction.ALLOW,
            reasons=["conversational_validation_skipped"],
        )

    def _failed_report(self, reason: str) -> HallucinationReport:
        risk = RiskAssessment(risk_level=RiskLevel.CRITICAL_RISK, risk_score=1.0, factors=["validation_pipeline_failed"])
        return HallucinationReport(
            valid=False,
            risk=risk,
            source_verification=SourceVerification(verified=False, unsupported_claims=[reason]),
            grounding=GroundingResult(grounded=False, violations=["validation_pipeline_failed"]),
            fact_check=FactCheckResult(passed=False, unsupported_claims=[reason], hallucination_indicators=["validation_pipeline_failed"]),
            action=ValidationAction.REJECT,
            reasons=["validation_pipeline_failed"],
        )
