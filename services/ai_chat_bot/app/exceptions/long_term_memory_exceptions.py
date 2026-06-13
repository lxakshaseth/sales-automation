from typing import Any


class LongTermMemoryError(RuntimeError):
    """Base class for production-safe long-term memory failures."""

    error_code = "long_term_memory_error"
    safe_message = "Long-term memory operation failed."

    def __init__(self, message: str | None = None, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message or self.safe_message)
        self.details = details or {}

    def to_response(self) -> dict[str, Any]:
        return {
            "error_code": self.error_code,
            "message": self.safe_message,
            "details": self.details,
        }


class MongoMemoryConnectionError(LongTermMemoryError):
    error_code = "mongo_memory_connection_error"
    safe_message = "MongoDB long-term memory store is unavailable."


class MemoryProfileError(LongTermMemoryError):
    error_code = "memory_profile_error"
    safe_message = "User memory profile could not be updated."


class MemoryInsightError(LongTermMemoryError):
    error_code = "memory_insight_error"
    safe_message = "Memory insight could not be stored."


class MemorySummaryError(LongTermMemoryError):
    error_code = "memory_summary_error"
    safe_message = "Conversation summary could not be stored."


class MemoryNotFoundError(LongTermMemoryError):
    error_code = "memory_not_found"
    safe_message = "Requested memory was not found."
