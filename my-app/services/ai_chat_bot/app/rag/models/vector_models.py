from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from app.rag.models.document_models import utc_now

SimilarityMetric = Literal["cosine", "l2", "dot_product"]


class VectorMetadata(BaseModel):
    chunk_id: str
    document_id: str
    source_filename: str | None = None
    chunk_index: int | None = Field(default=None, ge=0)
    token_count: int | None = Field(default=None, ge=0)
    page_number: int | None = Field(default=None, ge=1)
    embedding_provider: str = "sentence-transformers"
    embedding_version: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class DenseVector(BaseModel):
    vector_id: str
    chunk_id: str
    document_id: str
    embedding_model: str
    vector: list[float]
    vector_dimension: int = Field(ge=1)
    normalized: bool = True
    metadata: VectorMetadata
    created_at: datetime = Field(default_factory=utc_now)

    @field_validator("vector")
    @classmethod
    def validate_vector_values(cls, value: list[float]) -> list[float]:
        if not value:
            raise ValueError("vector cannot be empty")
        return [float(item) for item in value]


class StoredVector(BaseModel):
    vector_id: str
    chunk_id: str
    document_id: str
    embedding_model: str
    vector_dimension: int = Field(ge=1)
    normalized: bool = True
    metadata: VectorMetadata
    storage_index: int | None = Field(default=None, ge=0)
    stored_at: datetime = Field(default_factory=utc_now)


class VectorIndexConfig(BaseModel):
    index_name: str = "default"
    index_path: str = "data/vector_indexes/default"
    vector_dimension: int = Field(default=384, ge=1)
    similarity_metric: SimilarityMetric = "cosine"
    normalize_on_insert: bool = True
    persist_metadata: bool = True
    auto_persist: bool = False


class BatchVectorResult(BaseModel):
    success: bool
    stored_vectors: list[StoredVector] = Field(default_factory=list)
    errors: list[dict[str, Any]] = Field(default_factory=list)
    inserted_count: int = Field(default=0, ge=0)
    skipped_count: int = Field(default=0, ge=0)
    duration_ms: float | None = None
    indexed_at: datetime = Field(default_factory=utc_now)
