from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictConfidenceModel(BaseModel):
    """Strict model base for internal confidence decisions."""

    model_config = ConfigDict(extra="forbid", strict=True)


class ConfidenceLevel(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    VERY_LOW = "VERY_LOW"


class ConfidenceReason(StrictConfidenceModel):
    code: str
    message: str
    weight: float = Field(default=0.0, ge=0.0, le=1.0)
    source: Literal["retrieval", "tool", "intent", "response", "overall"] = "overall"

    @field_validator("code", "message")
    @classmethod
    def validate_non_empty_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("value cannot be empty")
        return normalized


class RetrievalConfidence(StrictConfidenceModel):
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel
    retrieval_supported: bool
    top_chunk_similarity: float = Field(default=0.0, ge=0.0, le=1.0)
    average_chunk_similarity: float = Field(default=0.0, ge=0.0, le=1.0)
    rerank_score: float = Field(default=0.0, ge=0.0, le=1.0)
    chunk_relevance: float = Field(default=0.0, ge=0.0, le=1.0)
    chunk_count: int = Field(default=0, ge=0)
    retrieval_threshold: float = Field(default=0.65, ge=0.0, le=1.0)
    reasons: list[ConfidenceReason] = Field(default_factory=list)


class ToolConfidence(StrictConfidenceModel):
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel
    tool_verified: bool
    tool_exists: bool = False
    parameters_validated: bool = False
    execution_success: bool = False
    returned_success_status: bool = False
    response_complete: bool = False
    reasons: list[ConfidenceReason] = Field(default_factory=list)


class ResponseConfidence(StrictConfidenceModel):
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel
    schema_valid: bool
    hallucination_risk: bool
    structured_output_valid: bool = False
    response_complete: bool = False
    uncertainty_detected: bool = False
    unsupported_claims_detected: bool = False
    reasons: list[ConfidenceReason] = Field(default_factory=list)


class ConfidenceMetrics(StrictConfidenceModel):
    retrieval_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    tool_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    intent_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    response_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    weights: dict[str, float] = Field(
        default_factory=lambda: {
            "retrieval_confidence": 0.40,
            "tool_confidence": 0.30,
            "intent_confidence": 0.15,
            "response_confidence": 0.15,
        }
    )

    @model_validator(mode="after")
    def validate_weights(self) -> "ConfidenceMetrics":
        required = {
            "retrieval_confidence",
            "tool_confidence",
            "intent_confidence",
            "response_confidence",
        }
        if set(self.weights) != required:
            raise ValueError("weights must contain retrieval, tool, intent, and response confidence keys")
        total = sum(self.weights.values())
        if total <= 0:
            raise ValueError("weights must be greater than zero")
        return self


class ConfidenceResult(StrictConfidenceModel):
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel
    reason: list[str] = Field(default_factory=list)
    recommendation: dict[str, str] = Field(default_factory=dict)
    indicators: dict[str, bool] = Field(default_factory=dict)
    metrics: ConfidenceMetrics
    reasoning_details: list[ConfidenceReason] = Field(default_factory=list)
    fallback_required: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConfidenceInput(StrictConfidenceModel):
    retrieval_score: float | None = Field(default=None, ge=0.0, le=1.0)
    rerank_score: float | None = Field(default=None, ge=0.0, le=1.0)
    chunk_relevance: float | None = Field(default=None, ge=0.0, le=1.0)
    chunk_scores: list[float] = Field(default_factory=list)
    chunk_count: int | None = Field(default=None, ge=0)
    retrieval_threshold: float = Field(default=0.65, ge=0.0, le=1.0)
    tool_output: dict[str, Any] | None = None
    tool_exists: bool | None = None
    parameters_validated: bool | None = None
    intent_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    llm_response: str | dict[str, Any] | None = None
    structured_output_valid: bool = False
    schema_validation_success: bool = False
    response_complete: bool | None = None
    unsupported_claims: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("chunk_scores")
    @classmethod
    def validate_chunk_scores(cls, value: list[float]) -> list[float]:
        for score in value:
            if score < 0.0 or score > 1.0:
                raise ValueError("chunk_scores must be between 0.0 and 1.0")
        return value
