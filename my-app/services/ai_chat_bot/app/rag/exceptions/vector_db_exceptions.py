from typing import Any


class VectorDBError(RuntimeError):
    """Base class for production-safe vector database failures."""

    error_code = "vector_db_error"
    safe_message = "Vector database operation failed."

    def __init__(self, message: str | None = None, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message or self.safe_message)
        self.details = details or {}

    def to_response(self) -> dict[str, Any]:
        return {
            "error_code": self.error_code,
            "message": self.safe_message,
            "details": self.details,
        }


class VectorIndexError(VectorDBError):
    error_code = "vector_index_error"
    safe_message = "Vector index operation failed."


class VectorPersistenceError(VectorDBError):
    error_code = "vector_persistence_error"
    safe_message = "Vector index persistence failed."


class VectorSearchError(VectorDBError):
    error_code = "vector_search_error"
    safe_message = "Vector search failed."


class VectorValidationError(VectorDBError):
    error_code = "vector_validation_error"
    safe_message = "Vector failed validation."


class DuplicateVectorError(VectorValidationError):
    error_code = "duplicate_vector_id"
    safe_message = "Vector ID already exists."


class MissingVectorError(VectorDBError):
    error_code = "missing_vector"
    safe_message = "Vector could not be found."

