from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.message_models import utc_now


class PerformanceMetrics(BaseModel):
    operation_name: str
    duration_ms: float = Field(default=0.0, ge=0.0)
    cache_hits: int = Field(default=0, ge=0)
    cache_misses: int = Field(default=0, ge=0)
    retrieval_latency_ms: float = Field(default=0.0, ge=0.0)
    embedding_latency_ms: float = Field(default=0.0, ge=0.0)
    token_count: int = Field(default=0, ge=0)
    concurrent_requests: int = Field(default=0, ge=0)
    success: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    measured_at: datetime = Field(default_factory=utc_now)

    @property
    def cache_hit_rate(self) -> float:
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total else 0.0


class PerformanceSnapshot(BaseModel):
    metrics: list[PerformanceMetrics] = Field(default_factory=list)
    total_operations: int = Field(default=0, ge=0)
    average_latency_ms: float = Field(default=0.0, ge=0.0)
    cache_hit_rate: float = Field(default=0.0, ge=0.0)
    generated_at: datetime = Field(default_factory=utc_now)

