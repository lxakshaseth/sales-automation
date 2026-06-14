from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.models.compression_models import TokenUsage
from app.models.message_models import utc_now


class MemoryOptimizationResult(BaseModel):
    success: bool
    user_id: str
    session_id: str | None = None
    original_message_count: int = Field(default=0, ge=0)
    retained_message_count: int = Field(default=0, ge=0)
    summarized_message_count: int = Field(default=0, ge=0)
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    summary_id: str | None = None
    cleanup_actions: list[str] = Field(default_factory=list)
    error: dict[str, Any] | None = None
    optimized_at: datetime = Field(default_factory=utc_now)


class MemoryCleanupResult(BaseModel):
    success: bool
    deleted_count: int = Field(default=0, ge=0)
    retained_count: int = Field(default=0, ge=0)
    actions: list[str] = Field(default_factory=list)
    error: dict[str, Any] | None = None
    cleaned_at: datetime = Field(default_factory=utc_now)


class OptimizationConfig(BaseModel):
    retrieval_cache_ttl_seconds: int = Field(default=900, ge=1)
    embedding_cache_ttl_seconds: int = Field(default=24 * 60 * 60, ge=1)
    response_cache_ttl_seconds: int = Field(default=300, ge=1)
    max_concurrency: int = Field(default=20, ge=1, le=1000)
    batch_size: int = Field(default=16, ge=1, le=1000)
    request_timeout_seconds: float = Field(default=30.0, ge=0.1)
    token_budget: int = Field(default=8192, ge=256)
    enable_in_memory_fallback: bool = True
    enable_cache_metrics: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class TokenUsage(BaseModel):
    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    saved_tokens: int = Field(default=0, ge=0)
    estimated_cost_units: float = Field(default=0.0, ge=0.0)
    model_name: str | None = None

    @field_validator("total_tokens")
    @classmethod
    def total_covers_parts(cls, value: int, info) -> int:
        prompt = info.data.get("prompt_tokens", 0)
        completion = info.data.get("completion_tokens", 0)
        return max(value, prompt + completion)


class OptimizationResult(BaseModel):
    success: bool
    operation: str
    cache_hit: bool = False
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    duration_ms: float | None = None
    result: Any = None
    error: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    optimized_at: datetime = Field(default_factory=utc_now)
