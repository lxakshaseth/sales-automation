from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.rag.models.document_models import DocumentChunk, utc_now
from app.rag.models.vector_models import DenseVector

DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_EMBEDDING_DIMENSION = 384


class EmbeddingConfig(BaseModel):
    model_name: str = DEFAULT_EMBEDDING_MODEL
    expected_dimension: int = Field(default=DEFAULT_EMBEDDING_DIMENSION, ge=1)
    normalize: bool = True
    batch_size: int = Field(default=32, ge=1, le=512)
    device: str | None = None
    cache_enabled: bool = True
    timeout_seconds: float | None = Field(default=None, gt=0)
    model_kwargs: dict[str, object] = Field(default_factory=dict)


class EmbeddingRequest(BaseModel):
    chunk: DocumentChunk
    config: EmbeddingConfig = Field(default_factory=EmbeddingConfig)

    @field_validator("chunk")
    @classmethod
    def validate_chunk_text(cls, value: DocumentChunk) -> DocumentChunk:
        if not value.content.strip():
            raise ValueError("chunk content cannot be empty")
        return value


class EmbeddingResponse(BaseModel):
    success: bool
    vector: DenseVector | None = None
    error: dict[str, object] | None = None
    cached: bool = False
    duration_ms: float | None = None
    embedded_at: datetime = Field(default_factory=utc_now)


class BatchEmbeddingResult(BaseModel):
    success: bool
    vectors: list[DenseVector] = Field(default_factory=list)
    errors: list[dict[str, object]] = Field(default_factory=list)
    cached_count: int = Field(default=0, ge=0)
    generated_count: int = Field(default=0, ge=0)
    total_chunks: int = Field(default=0, ge=0)
    duration_ms: float | None = None
    config: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    embedded_at: datetime = Field(default_factory=utc_now)

