from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictOrchestrationModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class RequestType(StrEnum):
    CHAT = "chat"
    RETRIEVAL = "retrieval"
    CRM = "crm"
    EMAIL = "email"
    CALENDAR = "calendar"
    TOOL_CALL = "tool_call"
    MULTILINGUAL = "multilingual"
    REASONING = "reasoning"
    AUTOMATION = "automation"


class ReasoningMode(StrEnum):
    SIMPLE_REPLY = "simple_reply"
    REASONING = "reasoning"
    RETRIEVAL = "retrieval"
    TOOL_EXECUTION = "tool_execution"
    MULTISTEP_REASONING = "multistep_reasoning"


class WorkflowStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"


class OrchestrationRequest(StrictOrchestrationModel):
    user_query: str
    user_id: str | None = None
    tenant_id: str = "default"
    session_id: str | None = None
    channel: str = "default"
    preferred_language: str | None = None
    persona: str | None = None
    request_type: RequestType | str | None = None
    system_prompt: str = "You are an enterprise AI automation assistant."
    conversation_history: list[dict[str, Any]] = Field(default_factory=list)
    crm_context: list[dict[str, Any]] = Field(default_factory=list)
    retrieved_chunks: list[dict[str, Any]] = Field(default_factory=list)
    tool_outputs: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: float = Field(default=30.0, gt=0.0)
    retry_limit: int = Field(default=1, ge=0)

    @field_validator("user_query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("user_query cannot be empty")
        return normalized


class ContextBundle(StrictOrchestrationModel):
    system_prompt: str
    current_query: str
    tool_results: list[dict[str, Any]] = Field(default_factory=list)
    retrieved_chunks: list[dict[str, Any]] = Field(default_factory=list)
    memory_summary: str = ""
    chat_history: list[dict[str, Any]] = Field(default_factory=list)
    crm_context: list[dict[str, Any]] = Field(default_factory=list)
    user_preferences: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReasoningPlan(StrictOrchestrationModel):
    request_type: RequestType
    mode: ReasoningMode
    reasoning_depth: Literal["low", "medium", "high"] = "low"
    use_retrieval: bool = False
    use_tool: bool = False
    tool_name: str | None = None
    steps: list[str] = Field(default_factory=list)


class DecisionResult(StrictOrchestrationModel):
    use_rag: bool = False
    use_tool: bool = False
    route_model: bool = True
    trigger_fallback: bool = False
    fallback_reason: str | None = None
    selected_tool: str | None = None
    confidence_action: str = "continue"
    reasons: list[str] = Field(default_factory=list)


class ExecutionTrace(StrictOrchestrationModel):
    step: str
    start_time: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    end_time: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    duration_ms: float = Field(default=0.0, ge=0.0)
    status: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value: WorkflowStatus | str) -> str:
        if isinstance(value, WorkflowStatus):
            if value == WorkflowStatus.COMPLETED:
                return "success"
            if value in {WorkflowStatus.FAILED, WorkflowStatus.ABORTED}:
                return "failed"
            return value.value.lower()
        return str(value).lower()


class PipelineMetrics(StrictOrchestrationModel):
    workflow_duration_ms: float = Field(default=0.0, ge=0.0)
    provider_latency_ms: float = Field(default=0.0, ge=0.0)
    retrieval_latency_ms: float = Field(default=0.0, ge=0.0)
    tool_latency_ms: float = Field(default=0.0, ge=0.0)
    token_usage: dict[str, Any] = Field(default_factory=dict)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    hallucination_risk: str | None = None


class WorkflowState(StrictOrchestrationModel):
    workflow_id: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    request: OrchestrationRequest
    context: ContextBundle | None = None
    reasoning_plan: ReasoningPlan | None = None
    decision: DecisionResult | None = None
    traces: list[ExecutionTrace] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowResult(StrictOrchestrationModel):
    success: bool
    response: str
    state: WorkflowState
    metrics: PipelineMetrics
    error: str | None = None


class OrchestrationResponse(StrictOrchestrationModel):
    success: bool
    response: str
    raw_response: str | None = None
    request_type: RequestType
    reasoning_mode: ReasoningMode
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    action: str = "respond"
    traces: list[ExecutionTrace] = Field(default_factory=list)
    metrics: PipelineMetrics = Field(default_factory=PipelineMetrics)
    metadata: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
