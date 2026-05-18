from typing import Any


class SummarizationError(RuntimeError):
    """Base class for production-safe memory summarization failures."""

    error_code = "summarization_error"
    safe_message = "Memory summarization failed."

    def __init__(self, message: str | None = None, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message or self.safe_message)
        self.details = details or {}

    def to_response(self) -> dict[str, Any]:
        return {
            "error_code": self.error_code,
            "message": self.safe_message,
            "details": self.details,
        }


class EmptyConversationError(SummarizationError):
    error_code = "empty_conversation"
    safe_message = "Conversation cannot be empty."


class SummaryGenerationError(SummarizationError):
    error_code = "summary_generation_error"
    safe_message = "Conversation summary could not be generated."


class CompressionError(SummarizationError):
    error_code = "compression_error"
    safe_message = "Conversation context could not be compressed."


class TokenOverflowError(SummarizationError):
    error_code = "token_overflow"
    safe_message = "Conversation context exceeds token budget."


class SummaryRepositoryError(SummarizationError):
    error_code = "summary_repository_error"
    safe_message = "Summary could not be persisted."
