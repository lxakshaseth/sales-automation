from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.rag.models.document_models import utc_now
from app.rag.models.vector_models import StoredVector
from app.rag.models.ranking_models import RankedChunk


class SearchQuery(BaseModel):
    query_vector: list[float]
    top_k: int = Field(default=5, ge=1, le=100)
    score_threshold: float | None = None
    metadata_filter: dict[str, Any] = Field(default_factory=dict)

    @field_validator("query_vector")
    @classmethod
    def validate_query_vector(cls, value: list[float]) -> list[float]:
        if not value:
            raise ValueError("query_vector cannot be empty")
        return [float(item) for item in value]


class SearchResult(BaseModel):
    vector_id: str
    chunk_id: str
    document_id: str
    score: float
    distance: float | None = None
    rank: int = Field(ge=1)
    stored_vector: StoredVector | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SimilarityResult(BaseModel):
    success: bool
    results: list[SearchResult] = Field(default_factory=list)
    error: dict[str, Any] | None = None
    query_top_k: int = Field(default=5, ge=1)
    returned_count: int = Field(default=0, ge=0)
    duration_ms: float | None = None
    searched_at: datetime = Field(default_factory=utc_now)


class SearchResponse(BaseModel):
    success: bool
    query: str
    results: list[RankedChunk] = Field(default_factory=list)
    error: dict[str, Any] | None = None
    returned_count: int = Field(default=0, ge=0)
    duration_ms: float | None = None
    searched_at: datetime = Field(default_factory=utc_now)
