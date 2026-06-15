"""RAG ingestion exceptions."""

from app.rag.exceptions.embedding_exceptions import (
    BatchEmbeddingError,
    EmbeddingError,
    EmbeddingGenerationError,
    EmbeddingModelLoadError,
    EmbeddingValidationError,
    EmptyChunkError,
)
from app.rag.exceptions.ingestion_exceptions import (
    CorruptedDocumentError,
    EmptyDocumentError,
    FileValidationError,
    IngestionError,
    UnsupportedFileTypeError,
)
from app.rag.exceptions.retrieval_exceptions import (
    EmptyQueryError,
    LowRelevanceError,
    QueryEmbeddingError,
    RerankingError,
    RetrievalError,
    RetrievalSearchError,
)
from app.rag.exceptions.vector_db_exceptions import (
    DuplicateVectorError,
    MissingVectorError,
    VectorDBError,
    VectorIndexError,
    VectorPersistenceError,
    VectorSearchError,
    VectorValidationError,
)

__all__ = [
    "BatchEmbeddingError",
    "CorruptedDocumentError",
    "EmbeddingError",
    "EmbeddingGenerationError",
    "EmbeddingModelLoadError",
    "EmbeddingValidationError",
    "EmptyDocumentError",
    "EmptyChunkError",
    "EmptyQueryError",
    "FileValidationError",
    "IngestionError",
    "LowRelevanceError",
    "DuplicateVectorError",
    "MissingVectorError",
    "QueryEmbeddingError",
    "RetrievalError",
    "RetrievalSearchError",
    "RerankingError",
    "UnsupportedFileTypeError",
    "VectorDBError",
    "VectorIndexError",
    "VectorPersistenceError",
    "VectorSearchError",
    "VectorValidationError",
]
