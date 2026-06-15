from typing import Any


class MemoryError(RuntimeError):
    """Base class for production-safe short-term memory failures."""

    error_code = "memory_error"
    safe_message = "Short-term memory operation failed."

    def __init__(self, message: str | None = None, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message or self.safe_message)
        self.details = details or {}

    def to_response(self) -> dict[str, Any]:
        return {
            "error_code": self.error_code,
            "message": self.safe_message,
            "details": self.details,
        }


class RedisMemoryConnectionError(MemoryError):
    error_code = "redis_memory_connection_error"
    safe_message = "Redis memory store is unavailable."


class MemorySerializationError(MemoryError):
    error_code = "memory_serialization_error"
    safe_message = "Memory payload could not be serialized."


class InvalidSessionError(MemoryError):
    error_code = "invalid_session"
    safe_message = "Session is invalid or expired."


class EmptyMessageError(MemoryError):
    error_code = "empty_message"
    safe_message = "Message text cannot be empty."


class DuplicateMessageError(MemoryError):
    error_code = "duplicate_message"
    safe_message = "Message already exists in memory."


class ContextWindowError(MemoryError):
    error_code = "context_window_error"
    safe_message = "Conversation context window could not be built."
