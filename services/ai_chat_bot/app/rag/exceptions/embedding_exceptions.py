from typing import Any


class EmbeddingError(RuntimeError):
    """Base class for production-safe embedding failures."""

    error_code = "embedding_error"
    safe_message = "Embedding generation failed."

    def __init__(self, message: str | None = None, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message or self.safe_message)
        self.details = details or {}

    def to_response(self) -> dict[str, Any]:
        return {
            "error_code": self.error_code,
            "message": self.safe_message,
            "details": self.details,
        }


class EmbeddingModelLoadError(EmbeddingError):
    error_code = "embedding_model_load_error"
    safe_message = "Embedding model could not be loaded."


class EmbeddingGenerationError(EmbeddingError):
    error_code = "embedding_generation_error"
    safe_message = "Embedding vector could not be generated."


class EmbeddingValidationError(EmbeddingError):
    error_code = "embedding_validation_error"
    safe_message = "Generated embedding failed validation."


class EmptyChunkError(EmbeddingError):
    error_code = "empty_chunk"
    safe_message = "Cannot embed an empty chunk."


class BatchEmbeddingError(EmbeddingError):
    error_code = "batch_embedding_error"
    safe_message = "Batch embedding generation failed."

