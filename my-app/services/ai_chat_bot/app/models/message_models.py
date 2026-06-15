from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


def utc_now() -> datetime:
    return datetime.now(UTC)


MessageRole = Literal["user", "assistant", "system", "tool"]


class ChatMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str
    user_id: str
    role: MessageRole
    message_text: str
    timestamp: datetime = Field(default_factory=utc_now)
    token_count: int = Field(default=0, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("message_text")
    @classmethod
    def validate_message_text(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("message_text cannot be empty")
        return normalized

    @field_validator("session_id", "user_id")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("identifier cannot be empty")
        return normalized
