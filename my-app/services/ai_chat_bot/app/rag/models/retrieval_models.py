from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from app.rag.models.document_models import utc_now
from app.rag.models.embedding_models import EmbeddingConfig
from app.rag.models.ranking_models import RankedChunk

RetrievalMode = Literal["semantic", "hybrid"]


class RetrievalConfig(BaseModel):
    top_k: int = Field(default=5, ge=1, le=100)
    candidate_k: int = Field(default=12, ge=1, le=200)
    relevance_threshold: float = Field(default=0.65, ge=0.0, le=1.0)
    similarity_weight: float = Field(default=0.75, ge=0.0, le=1.0)
    keyword_weight: float = Field(default=0.25, ge=0.0, le=1.0)
    enable_query_expansion: bool = True
    enable_reranking: bool = True
    enable_cache: bool = True
    retrieval_mode: RetrievalMode = "semantic"
    embedding_config: EmbeddingConfig = Field(default_factory=EmbeddingConfig)

    @field_validator("candidate_k")
    @classmethod
    def candidate_must_cover_top_k(cls, value: int, info) -> int:
        top_k = info.data.get("top_k", 5)
        return max(value, top_k)


class RetrievalRequest(BaseModel):
    query: str
    config: RetrievalConfig = Field(default_factory=RetrievalConfig)
    metadata_filter: dict[str, Any] = Field(default_factory=dict)
    request_id: str | None = None

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("query cannot be empty")
        return normalized


class RetrievalResult(BaseModel):
    success: bool
    query: str
    expanded_queries: list[str] = Field(default_factory=list)
    chunks: list[RankedChunk] = Field(default_factory=list)
    error: dict[str, Any] | None = None
    warnings: list[str] = Field(default_factory=list)
    returned_count: int = Field(default=0, ge=0)
    duration_ms: float | None = None
    retrieved_at: datetime = Field(default_factory=utc_now)

