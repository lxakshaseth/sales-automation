"""Application exception classes."""

from app.exceptions.memory_exceptions import (
    ContextWindowError,
    DuplicateMessageError,
    EmptyMessageError,
    InvalidSessionError,
    MemoryError,
    MemorySerializationError,
    RedisMemoryConnectionError,
)
from app.exceptions.long_term_memory_exceptions import (
    LongTermMemoryError,
    MemoryInsightError,
    MemoryNotFoundError,
    MemoryProfileError,
    MemorySummaryError,
    MongoMemoryConnectionError,
)
from app.exceptions.summarization_exceptions import (
    CompressionError,
    EmptyConversationError,
    SummarizationError,
    SummaryGenerationError,
    SummaryRepositoryError,
    TokenOverflowError,
)

__all__ = [
    "ContextWindowError",
    "CompressionError",
    "DuplicateMessageError",
    "EmptyConversationError",
    "EmptyMessageError",
    "InvalidSessionError",
    "LongTermMemoryError",
    "MemoryError",
    "MemoryInsightError",
    "MemoryNotFoundError",
    "MemoryProfileError",
    "MemorySerializationError",
    "MemorySummaryError",
    "MongoMemoryConnectionError",
    "RedisMemoryConnectionError",
    "SummarizationError",
    "SummaryGenerationError",
    "SummaryRepositoryError",
    "TokenOverflowError",
]
