from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


def utc_now() -> datetime:
    return datetime.now(UTC)


InsightType = Literal["preference", "fact", "intent", "constraint", "business_context", "follow_up", "semantic_note"]


class UserPreference(BaseModel):
    key: str
    value: str
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    source: str = "conversation"
    updated_at: datetime = Field(default_factory=utc_now)


class MemoryInsight(BaseModel):
    insight_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    insight_type: InsightType = "semantic_note"
    content: str
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    source_session_id: str | None = None
    source_conversation_id: str | None = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("user_id", "content")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("value cannot be empty")
        return normalized


class ConversationSummaryMemory(BaseModel):
    summary_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    summary: str
    session_id: str | None = None
    conversation_id: str | None = None
    intents: list[str] = Field(default_factory=list)
    entities: dict[str, Any] = Field(default_factory=dict)
    sentiment: str | None = None
    language: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)

    @field_validator("user_id", "summary")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("value cannot be empty")
        return normalized


class UserMemoryProfile(BaseModel):
    user_id: str
    preferences: dict[str, UserPreference] = Field(default_factory=dict)
    known_facts: list[str] = Field(default_factory=list)
    recurring_intents: list[str] = Field(default_factory=list)
    semantic_profile: str = ""
    last_summary: str | None = None
    memory_version: int = Field(default=1, ge=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("user_id cannot be empty")
        return normalized


class LongTermMemoryConfig(BaseModel):
    profile_collection: str = "ai_user_memory_profiles"
    summary_collection: str = "ai_conversation_memories"
    insight_collection: str = "ai_memory_insights"
    max_profile_facts: int = Field(default=50, ge=1, le=500)
    max_recurring_intents: int = Field(default=30, ge=1, le=200)
    min_insight_confidence: float = Field(default=0.4, ge=0.0, le=1.0)


class LongTermMemorySnapshot(BaseModel):
    user_id: str
    profile: UserMemoryProfile | None = None
    summaries: list[ConversationSummaryMemory] = Field(default_factory=list)
    insights: list[MemoryInsight] = Field(default_factory=list)
    retrieved_at: datetime = Field(default_factory=utc_now)
