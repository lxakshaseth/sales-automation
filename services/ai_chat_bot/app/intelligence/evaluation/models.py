from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictEvaluationModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class EvaluationStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"


class DeploymentStatus(StrEnum):
    APPROVED = "APPROVED"
    WARNING = "WARNING"
    REJECTED = "REJECTED"


class BenchmarkCategory(StrEnum):
    RAG = "rag"
    TOOL_CALLING = "tool_calling"
    PROMPT = "prompt"
    HALLUCINATION = "hallucination"
    LATENCY = "latency"
    TOKEN_EFFICIENCY = "token_efficiency"
    REGRESSION = "regression"


class BenchmarkCase(StrictEvaluationModel):
    question: str
    expected_answer: str | None = None
    expected_tool: str | None = None
    expected_intent: str | None = None
    expected_retrieval: list[str] = Field(default_factory=list)
    expected_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    actual_answer: str | None = None
    actual_tool: str | None = None
    actual_parameters: dict[str, Any] = Field(default_factory=dict)
    expected_parameters: dict[str, Any] = Field(default_factory=dict)
    retrieved_chunks: list[dict[str, Any]] = Field(default_factory=list)
    latency_ms: float | None = Field(default=None, ge=0.0)
    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    original_tokens: int = Field(default=0, ge=0)
    optimized_tokens: int = Field(default=0, ge=0)
    unsupported_claims: list[str] = Field(default_factory=list)
    tool_success: bool | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("question cannot be empty")
        return normalized


class HallucinationMetrics(StrictEvaluationModel):
    hallucination_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    unsupported_claim_count: int = Field(default=0, ge=0)
    source_grounding_accuracy: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_alignment: float = Field(default=0.0, ge=0.0, le=1.0)


class RetrievalMetrics(StrictEvaluationModel):
    recall_at_k: float = Field(default=0.0, ge=0.0, le=1.0)
    precision_at_k: float = Field(default=0.0, ge=0.0, le=1.0)
    retrieval_relevance: float = Field(default=0.0, ge=0.0, le=1.0)
    chunk_usefulness: float = Field(default=0.0, ge=0.0, le=1.0)
    reranker_quality: float = Field(default=0.0, ge=0.0, le=1.0)


class ToolMetrics(StrictEvaluationModel):
    tool_selection_accuracy: float = Field(default=0.0, ge=0.0, le=1.0)
    parameter_extraction_accuracy: float = Field(default=0.0, ge=0.0, le=1.0)
    execution_success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    hallucinated_tool_call_rate: float = Field(default=0.0, ge=0.0, le=1.0)


class LatencyMetrics(StrictEvaluationModel):
    avg_latency_ms: float = Field(default=0.0, ge=0.0)
    p95_latency_ms: float = Field(default=0.0, ge=0.0)
    max_latency_ms: float = Field(default=0.0, ge=0.0)


class TokenMetrics(StrictEvaluationModel):
    average_prompt_tokens: float = Field(default=0.0, ge=0.0)
    average_completion_tokens: float = Field(default=0.0, ge=0.0)
    token_reduction: float = Field(default=0.0, ge=0.0)
    average_total_tokens: float = Field(default=0.0, ge=0.0)


class EvaluationResult(StrictEvaluationModel):
    name: str
    category: BenchmarkCategory
    score: float = Field(ge=0.0, le=100.0)
    status: EvaluationStatus
    passed: bool
    metrics: dict[str, Any] = Field(default_factory=dict)
    case_count: int = Field(default=0, ge=0)
    failures: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BenchmarkResult(StrictEvaluationModel):
    benchmark_name: str
    category: BenchmarkCategory
    score: float = Field(ge=0.0, le=100.0)
    status: EvaluationStatus
    results: list[EvaluationResult] = Field(default_factory=list)
    case_count: int = Field(default=0, ge=0)
    duration_ms: float = Field(default=0.0, ge=0.0)
    report: dict[str, Any] = Field(default_factory=dict)


class RegressionResult(StrictEvaluationModel):
    passed: bool
    baseline_score: float = Field(default=0.0, ge=0.0, le=100.0)
    current_score: float = Field(default=0.0, ge=0.0, le=100.0)
    quality_drop: float = Field(default=0.0, ge=0.0)
    threshold: float = Field(default=5.0, ge=0.0)
    failures: list[str] = Field(default_factory=list)


class DeploymentDecision(StrictEvaluationModel):
    overall_score: float = Field(ge=0.0, le=100.0)
    deployment_status: DeploymentStatus
    approved: bool
    reasons: list[str] = Field(default_factory=list)
    blocking_failures: list[str] = Field(default_factory=list)


class EvaluationReport(StrictEvaluationModel):
    overall_score: float = Field(ge=0.0, le=100.0)
    deployment_decision: DeploymentDecision
    benchmark_results: list[BenchmarkResult] = Field(default_factory=list)
    regression_result: RegressionResult | None = None
    metrics_summary: dict[str, Any] = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)
