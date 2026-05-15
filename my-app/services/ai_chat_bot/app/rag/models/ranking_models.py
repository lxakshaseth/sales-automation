from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.rag.models.document_models import utc_now


class RelevanceScore(BaseModel):
    similarity_score: float = Field(ge=-1.0, le=1.0)
    rerank_score: float = Field(ge=0.0, le=1.0)
    final_score: float = Field(ge=0.0, le=1.0)
    score_reason: str = ""
    created_at: datetime = Field(default_factory=utc_now)


class RankedChunk(BaseModel):
    chunk_id: str
    document_id: str
    vector_id: str
    rank: int = Field(ge=1)
    similarity_score: float
    rerank_score: float = Field(default=0.0, ge=0.0, le=1.0)
    final_score: float = Field(default=0.0, ge=0.0, le=1.0)
    source_filename: str | None = None
    content: str | None = None
    chunk_metadata: dict[str, Any] = Field(default_factory=dict)
    retrieval_metadata: dict[str, Any] = Field(default_factory=dict)
    retrieved_at: datetime = Field(default_factory=utc_now)

