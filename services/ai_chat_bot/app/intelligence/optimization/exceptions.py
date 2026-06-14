class TokenOptimizationError(Exception):
    """Base exception for token optimization failures."""


class TokenCounterError(TokenOptimizationError):
    """Raised when token counting fails."""


class ContextOptimizationError(TokenOptimizationError):
    """Raised when context optimization cannot complete normally."""


class ContextOverflowError(TokenOptimizationError):
    """Raised when context still exceeds budget after safe optimization."""


class CacheOptimizationError(TokenOptimizationError):
    """Raised when optimization cache operations fail."""
