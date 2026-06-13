from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictSafetyModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class RiskLevel(StrEnum):
    LOW_RISK = "LOW_RISK"
    MEDIUM_RISK = "MEDIUM_RISK"
    HIGH_RISK = "HIGH_RISK"
    CRITICAL_RISK = "CRITICAL_RISK"


class ValidationAction(StrEnum):
    ALLOW = "allow"
    WARNING = "clarification_required"
    REJECT = "fallback_response"


class SourceVerification(StrictSafetyModel):
    verified: bool
    coverage: float = Field(default=0.0, ge=0.0, le=1.0)
    matched_claims: list[str] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    evidence_sources: list[str] = Field(default_factory=list)
    missing_sources: list[str] = Field(default_factory=list)


class GroundingResult(StrictSafetyModel):
    grounded: bool
    retrieval_grounded: bool = False
    tool_grounded: bool = False
    memory_grounded: bool = False
    tool_failures: list[str] = Field(default_factory=list)
    violations: list[str] = Field(default_factory=list)


class FactCheckResult(StrictSafetyModel):
    passed: bool
    factual_consistency: float = Field(default=0.0, ge=0.0, le=1.0)
    verified_claims: list[str] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    hallucination_indicators: list[str] = Field(default_factory=list)


class RiskAssessment(StrictSafetyModel):
    risk_level: RiskLevel
    risk_score: float = Field(ge=0.0, le=1.0)
    factors: list[str] = Field(default_factory=list)
    source_coverage: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class FallbackResponse(StrictSafetyModel):
    action: ValidationAction = ValidationAction.REJECT
    response: str
    reason: str

    @field_validator("response", "reason")
    @classmethod
    def validate_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("fallback text cannot be empty")
        return normalized


class HallucinationReport(StrictSafetyModel):
    valid: bool
    risk: RiskAssessment
    source_verification: SourceVerification
    grounding: GroundingResult
    fact_check: FactCheckResult
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    action: ValidationAction
    reasons: list[str] = Field(default_factory=list)


class ValidationResult(StrictSafetyModel):
    valid: bool
    action: ValidationAction
    response: str
    original_response: str
    report: HallucinationReport
    fallback: FallbackResponse | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ValidationInput(StrictSafetyModel):
    response: str
    retrieved_chunks: list[dict[str, Any]] = Field(default_factory=list)
    tool_outputs: list[dict[str, Any]] = Field(default_factory=list)
    memory_context: list[dict[str, Any]] = Field(default_factory=list)
    system_context: list[dict[str, Any]] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_result: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("response")
    @classmethod
    def validate_response(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("response cannot be empty")
        return normalized
