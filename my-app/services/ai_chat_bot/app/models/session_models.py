from datetime import datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from app.models.message_models import utc_now

SessionStatus = Literal["active", "expired", "closed"]


class SessionMetadata(BaseModel):
    channel: str = "chat"
    device_id: str | None = None
    source: str | None = None
    language: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class SessionState(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    status: SessionStatus = "active"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime | None = None
    message_count: int = Field(default=0, ge=0)
    metadata: SessionMetadata = Field(default_factory=SessionMetadata)

    @field_validator("session_id", "user_id")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("identifier cannot be empty")
        return normalized
