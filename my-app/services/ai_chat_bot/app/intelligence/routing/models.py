from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictRoutingModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ProviderState(StrEnum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    DISABLED = "DISABLED"


class TaskType(StrEnum):
    QUICK_REPLY = "quick_reply"
    REASONING = "reasoning"
    TOOL_CALLING = "tool_calling"
    RETRIEVAL = "retrieval"
    RAG_HEAVY = "RAG_heavy"
    MULTILINGUAL = "multilingual"
    SUMMARIZATION = "summarization"
    CLASSIFICATION = "classification"
    CONVERSATION = "conversation"


class RoutingStrategy(StrEnum):
    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUTING = "weighted_routing"
    LEAST_LATENCY = "least_latency"
    LEAST_COST = "least_cost"


class ProviderConfig(StrictRoutingModel):
    name: str
    enabled: bool = False
    api_key_env: str | None = None
    api_key: str | None = None
    base_url_env: str | None = None
    base_url: str | None = None
    default_model: str | None = None
    model_aliases: dict[str, str] = Field(default_factory=dict)
    priority: int = Field(default=100, ge=1)
    timeout_seconds: float = Field(default=30.0, gt=0.0)
    retry_limit: int = Field(default=2, ge=0)
    cooldown_seconds: float = Field(default=60.0, ge=0.0)
    weight: float = Field(default=1.0, ge=0.0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("provider name cannot be empty")
        return normalized


class ProviderHealth(StrictRoutingModel):
    status: ProviderState = ProviderState.DISABLED
    average_latency_ms: float = Field(default=0.0, ge=0.0)
    failure_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    timeout_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    request_volume: int = Field(default=0, ge=0)
    consecutive_failures: int = Field(default=0, ge=0)
    cooldown_until_epoch: float | None = None
    last_error: str | None = None


class ProviderStatus(StrictRoutingModel):
    provider: str
    available: bool
    configured: bool
    health: ProviderHealth
    enabled: bool
    active_model_count: int = Field(default=0, ge=0)


class ModelCapability(StrictRoutingModel):
    model: str
    provider: str
    context_window: int = Field(default=8192, ge=1)
    multilingual_support: bool = False
    tool_calling_support: bool = False
    retrieval_support: bool = False
    reasoning_score: float = Field(default=0.5, ge=0.0, le=1.0)
    latency_score: float = Field(default=0.5, ge=0.0, le=1.0)
    cost_score: float = Field(default=0.5, ge=0.0, le=1.0)
    quality_score: float = Field(default=0.5, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RoutingRequest(StrictRoutingModel):
    messages: list[dict[str, str]] = Field(default_factory=list)
    prompt: str | None = None
    task_type: TaskType | str | None = None
    preferred_provider: str | None = None
    preferred_model: str | None = None
    require_tool_calling: bool = False
    require_multilingual: bool = False
    require_retrieval: bool = False
    optimize_for: Literal["balanced", "latency", "cost", "quality"] = "balanced"
    max_tokens: int | None = Field(default=None, ge=1)
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    timeout_seconds: float | None = Field(default=None, gt=0.0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_content(self) -> "RoutingRequest":
        if not self.messages and not self.prompt:
            raise ValueError("messages or prompt is required")
        return self


class RoutingDecision(StrictRoutingModel):
    provider: str
    model: str
    task_type: str
    strategy: RoutingStrategy = RoutingStrategy.WEIGHTED_ROUTING
    reason: list[str] = Field(default_factory=list)
    estimated_latency_score: float = Field(default=0.0, ge=0.0, le=1.0)
    estimated_cost_score: float = Field(default=0.0, ge=0.0, le=1.0)
    fallback_chain: list[str] = Field(default_factory=list)


class FallbackDecision(StrictRoutingModel):
    activated: bool = False
    from_provider: str | None = None
    from_model: str | None = None
    to_provider: str | None = None
    to_model: str | None = None
    attempt: int = Field(default=0, ge=0)
    reason: str | None = None
    exhausted: bool = False


class RoutingResponse(StrictRoutingModel):
    success: bool
    content: str | None = None
    provider: str | None = None
    model: str | None = None
    decision: RoutingDecision | None = None
    fallback: FallbackDecision | None = None
    latency_ms: float = Field(default=0.0, ge=0.0)
    error: str | None = None
    error_type: str | None = None
    raw_response: dict[str, Any] = Field(default_factory=dict)
