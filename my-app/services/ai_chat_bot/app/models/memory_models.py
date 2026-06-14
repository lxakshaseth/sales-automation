from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.message_models import ChatMessage, utc_now
from app.models.session_models import SessionState


class MemoryConfig(BaseModel):
    max_messages: int = Field(default=10, ge=1, le=200)
    token_limit: int = Field(default=4000, ge=100)
    session_ttl_seconds: int = Field(default=24 * 60 * 60, ge=60)
    redis_key_prefix: str = "memory"
    cache_enabled: bool = True
    duplicate_check_limit: int = Field(default=50, ge=1, le=500)


class MemoryEntry(BaseModel):
    message: ChatMessage
    stored_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ContextWindow(BaseModel):
    session_id: str
    user_id: str
    messages: list[ChatMessage] = Field(default_factory=list)
    token_count: int = Field(default=0, ge=0)
    max_messages: int = Field(default=10, ge=1)
    token_limit: int = Field(default=4000, ge=100)
    trimmed_count: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=utc_now)


class ConversationMemory(BaseModel):
    session: SessionState
    context_window: ContextWindow
    recent_messages: list[ChatMessage] = Field(default_factory=list)
    retrieved_at: datetime = Field(default_factory=utc_now)
