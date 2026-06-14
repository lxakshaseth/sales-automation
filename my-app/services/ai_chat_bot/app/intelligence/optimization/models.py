from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictOptimizationModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ContextPriority(StrEnum):
    SYSTEM_PROMPT = "system_prompt"
    CURRENT_USER_QUERY = "current_user_query"
    TOOL_OUTPUTS = "tool_outputs"
    RETRIEVAL_RESULTS = "retrieval_results"
    MEMORY_SUMMARY = "memory_summary"
    HISTORICAL_MESSAGES = "historical_messages"


class TokenBudget(StrictOptimizationModel):
    max_context_tokens: int = Field(default=12000, ge=512)
    max_rag_tokens: int = Field(default=4000, ge=0)
    max_history_tokens: int = Field(default=3000, ge=0)
    max_tool_output_tokens: int = Field(default=1000, ge=0)
    max_system_prompt_tokens: int = Field(default=1000, ge=0)
    reserved_response_tokens: int = Field(default=1000, ge=0)
    model_name: str | None = None

    @property
    def available_input_tokens(self) -> int:
        return max(0, self.max_context_tokens - self.reserved_response_tokens)


class TokenUsage(StrictOptimizationModel):
    system_prompt_tokens: int = Field(default=0, ge=0)
    user_query_tokens: int = Field(default=0, ge=0)
    rag_tokens: int = Field(default=0, ge=0)
    history_tokens: int = Field(default=0, ge=0)
    tool_output_tokens: int = Field(default=0, ge=0)
    memory_summary_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def total_covers_parts(self) -> "TokenUsage":
        calculated = (
            self.system_prompt_tokens
            + self.user_query_tokens
            + self.rag_tokens
            + self.history_tokens
            + self.tool_output_tokens
            + self.memory_summary_tokens
        )
        self.total_tokens = max(self.total_tokens, calculated)
        return self


class TokenAllocation(StrictOptimizationModel):
    priority: ContextPriority
    token_limit: int = Field(ge=0)
    allocated_tokens: int = Field(default=0, ge=0)
    trimmed_tokens: int = Field(default=0, ge=0)


class ContextMetrics(StrictOptimizationModel):
    rag_chunk_count: int = Field(default=0, ge=0)
    history_message_count: int = Field(default=0, ge=0)
    tool_output_count: int = Field(default=0, ge=0)
    duplicate_count: int = Field(default=0, ge=0)
    dropped_low_value_chunks: int = Field(default=0, ge=0)
    trimmed_sections: list[str] = Field(default_factory=list)


class CompressionResult(StrictOptimizationModel):
    success: bool
    original_tokens: int = Field(default=0, ge=0)
    compressed_tokens: int = Field(default=0, ge=0)
    saved_tokens: int = Field(default=0, ge=0)
    compression_ratio: float = Field(default=0.0, ge=0.0)
    duplicate_removed: int = Field(default=0, ge=0)
    output: Any = None
    warnings: list[str] = Field(default_factory=list)


class MemorySummary(StrictOptimizationModel):
    summary: str
    preserved_goals: list[str] = Field(default_factory=list)
    preserved_decisions: list[str] = Field(default_factory=list)
    crm_notes: list[str] = Field(default_factory=list)
    active_tasks: list[str] = Field(default_factory=list)
    original_message_count: int = Field(default=0, ge=0)
    summarized_message_count: int = Field(default=0, ge=0)
    token_usage: TokenUsage = Field(default_factory=TokenUsage)

    @field_validator("summary")
    @classmethod
    def validate_summary(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("summary cannot be empty")
        return normalized


class OptimizationReport(StrictOptimizationModel):
    original_tokens: int = Field(default=0, ge=0)
    optimized_tokens: int = Field(default=0, ge=0)
    saved_tokens: int = Field(default=0, ge=0)
    compression_ratio: float = Field(default=0.0, ge=0.0)
    overflow_prevented: bool = False
    fallback_used: bool = False
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    allocations: list[TokenAllocation] = Field(default_factory=list)
    metrics: ContextMetrics = Field(default_factory=ContextMetrics)
    warnings: list[str] = Field(default_factory=list)


class OptimizedContext(StrictOptimizationModel):
    system_prompt: str = ""
    user_query: str
    rag_context: list[dict[str, Any]] = Field(default_factory=list)
    history: list[dict[str, Any]] = Field(default_factory=list)
    memory_summary: str = ""
    tool_outputs: list[dict[str, Any]] = Field(default_factory=list)
    final_prompt: str = ""
    report: OptimizationReport
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("user_query")
    @classmethod
    def validate_user_query(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("user_query cannot be empty")
        return normalized
