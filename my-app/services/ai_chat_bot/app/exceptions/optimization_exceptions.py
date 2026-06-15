class OptimizationError(Exception):
    """Base exception for production optimization failures."""


class CacheOperationError(OptimizationError):
    """Raised when cache read/write/invalidation fails."""


class BatchProcessingError(OptimizationError):
    """Raised when a batch cannot be processed safely."""


class AsyncExecutionError(OptimizationError):
    """Raised when async pipeline execution fails."""


class ConcurrencyLimitError(OptimizationError):
    """Raised when request concurrency exceeds configured limits."""


class OptimizationRateLimitError(OptimizationError):
    """Raised when optimization-layer rate limits are exceeded."""


class OptimizationTokenError(OptimizationError):
    """Raised when token optimization cannot satisfy the budget."""

