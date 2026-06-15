from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from app.models.message_models import ChatMessage, utc_now


class TokenUsage(BaseModel):
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    saved_tokens: int = Field(default=0, ge=0)
    compression_ratio: float = Field(default=0.0, ge=0.0)
    model_name: str | None = None


class CompressedContext(BaseModel):
    context_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    session_id: str | None = None
    compressed_text: str
    preserved_messages: list[ChatMessage] = Field(default_factory=list)
    removed_message_count: int = Field(default=0, ge=0)
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    semantic_markers: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)

    @field_validator("compressed_text")
    @classmethod
    def validate_compressed_text(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("compressed_text cannot be empty")
        return normalized


class CompressionResult(BaseModel):
    success: bool
    compressed_context: CompressedContext | None = None
    error: dict[str, Any] | None = None
    warnings: list[str] = Field(default_factory=list)
    duration_ms: float | None = None
    compressed_at: datetime = Field(default_factory=utc_now)
