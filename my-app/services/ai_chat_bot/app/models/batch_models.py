from datetime import datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from app.models.message_models import utc_now


BatchType = Literal["embedding", "retrieval", "memory", "generic"]


class BatchRequest(BaseModel):
    batch_id: str = Field(default_factory=lambda: str(uuid4()))
    batch_type: BatchType = "generic"
    items: list[Any] = Field(default_factory=list)
    batch_size: int = Field(default=16, ge=1, le=1000)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)

    @field_validator("items")
    @classmethod
    def validate_items(cls, value: list[Any]) -> list[Any]:
        if not value:
            raise ValueError("batch items cannot be empty")
        return value


class BatchItemResult(BaseModel):
    index: int = Field(ge=0)
    success: bool
    value: Any = None
    error: dict[str, Any] | None = None


class BatchResult(BaseModel):
    batch_id: str
    batch_type: BatchType
    success: bool
    results: list[BatchItemResult] = Field(default_factory=list)
    total_items: int = Field(default=0, ge=0)
    successful_items: int = Field(default=0, ge=0)
    failed_items: int = Field(default=0, ge=0)
    duration_ms: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    completed_at: datetime = Field(default_factory=utc_now)

