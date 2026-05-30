from datetime import datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from app.models.message_models import ChatMessage, utc_now

ContextSource = Literal["retrieval", "short_term_memory", "long_term_memory", "summary_memory"]


class TokenBudget(BaseModel):
    model_name: str = "llama-3.3-70b-versatile"
    max_context_tokens: int = Field(default=8192, ge=512)
    reserved_response_tokens: int = Field(default=1024, ge=128)
    system_prompt_tokens: int = Field(default=800, ge=0)
    retrieval_token_ratio: float = Field(default=0.5, ge=0.0, le=1.0)
    memory_token_ratio: float = Field(default=0.3, ge=0.0, le=1.0)
    summary_token_ratio: float = Field(default=0.2, ge=0.0, le=1.0)

    @property
    def available_context_tokens(self) -> int:
        available = self.max_context_tokens - self.reserved_response_tokens - self.system_prompt_tokens
        return max(256, available)


class RetrievalContext(BaseModel):
    context_id: str = Field(default_factory=lambda: str(uuid4()))
    chunk_id: str | None = None
    document_id: str | None = None
    source_name: str | None = None
    content: str
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    rank: int | None = Field(default=None, ge=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    token_count: int = Field(default=0, ge=0)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("retrieval content cannot be empty")
        return normalized


class MemoryContext(BaseModel):
    context_id: str = Field(default_factory=lambda: str(uuid4()))
    memory_type: ContextSource
    content: str
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    recency_score: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    token_count: int = Field(default=0, ge=0)
    created_at: datetime | None = None

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("memory content cannot be empty")
        return normalized


class ContextMetadata(BaseModel):
    user_id: str | None = None
    session_id: str | None = None
    language_hint: str | None = None
    retrieval_count: int = Field(default=0, ge=0)
    memory_count: int = Field(default=0, ge=0)
    selected_retrieval_count: int = Field(default=0, ge=0)
    selected_memory_count: int = Field(default=0, ge=0)
    ranking_strategy: str = "lexical_semantic_weighted"
    hallucination_controls: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class PromptContext(BaseModel):
    user_query: str
    retrieved_context: list[RetrievalContext] = Field(default_factory=list)
    short_term_memory: list[MemoryContext] = Field(default_factory=list)
    long_term_memory: list[MemoryContext] = Field(default_factory=list)
    summarized_memory: list[MemoryContext] = Field(default_factory=list)
    metadata: ContextMetadata = Field(default_factory=ContextMetadata)

    @field_validator("user_query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("user_query cannot be empty")
        return normalized


class FinalContext(BaseModel):
    user_query: str
    final_prompt: str
    messages: list[dict[str, str]] = Field(default_factory=list)
    retrieved_context: list[RetrievalContext] = Field(default_factory=list)
    short_term_memory: list[MemoryContext] = Field(default_factory=list)
    long_term_memory: list[MemoryContext] = Field(default_factory=list)
    summarized_memory: list[MemoryContext] = Field(default_factory=list)
    semantic_metadata: ContextMetadata = Field(default_factory=ContextMetadata)
    token_usage: dict[str, Any] = Field(default_factory=dict)
    token_budget: TokenBudget = Field(default_factory=TokenBudget)
    created_at: datetime = Field(default_factory=utc_now)

    @field_validator("final_prompt")
    @classmethod
    def validate_prompt(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("final_prompt cannot be empty")
        return normalized


def chat_message_to_memory_context(message: ChatMessage) -> MemoryContext:
    return MemoryContext(
        memory_type="short_term_memory",
        content=f"{message.role}: {message.message_text}",
        importance=0.65 if message.role == "user" else 0.55,
        recency_score=0.9,
        confidence=0.8,
        metadata={
            "message_id": message.message_id,
            "session_id": message.session_id,
            "user_id": message.user_id,
            "timestamp": message.timestamp.isoformat(),
        },
        created_at=message.timestamp,
    )

