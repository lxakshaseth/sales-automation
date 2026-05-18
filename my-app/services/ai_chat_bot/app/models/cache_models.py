from datetime import datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from app.models.message_models import utc_now


CacheNamespace = Literal["retrieval", "embedding", "response", "semantic_query"]


class CacheEntry(BaseModel):
    key: str
    namespace: CacheNamespace
    value: Any
    ttl_seconds: int = Field(default=900, ge=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)

    @field_validator("key")
    @classmethod
    def validate_key(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("cache key cannot be empty")
        return normalized


class RetrievalCache(BaseModel):
    query: str
    cache_key: str
    results: list[dict[str, Any]] = Field(default_factory=list)
    hit: bool = False
    ttl_seconds: int = Field(default=900, ge=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EmbeddingCache(BaseModel):
    text: str
    cache_key: str
    embedding: list[float] = Field(default_factory=list)
    hit: bool = False
    ttl_seconds: int = Field(default=24 * 60 * 60, ge=1)
    model_name: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CacheResult(BaseModel):
    success: bool
    hit: bool = False
    key: str | None = None
    namespace: CacheNamespace | None = None
    value: Any = None
    error: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    cache_id: str = Field(default_factory=lambda: str(uuid4()))
    completed_at: datetime = Field(default_factory=utc_now)

