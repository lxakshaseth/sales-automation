"""Compatibility exports for embedding Pydantic models."""

from app.rag.models.embedding_models import (
    DEFAULT_EMBEDDING_DIMENSION,
    DEFAULT_EMBEDDING_MODEL,
    BatchEmbeddingResult,
    EmbeddingConfig,
    EmbeddingRequest,
    EmbeddingResponse,
)
from app.rag.models.vector_models import DenseVector, VectorMetadata

__all__ = [
    "BatchEmbeddingResult",
    "DEFAULT_EMBEDDING_DIMENSION",
    "DEFAULT_EMBEDDING_MODEL",
    "DenseVector",
    "EmbeddingConfig",
    "EmbeddingRequest",
    "EmbeddingResponse",
    "VectorMetadata",
]

