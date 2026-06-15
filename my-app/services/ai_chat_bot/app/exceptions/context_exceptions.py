class ContextBuilderError(Exception):
    """Base exception for R9 context builder failures."""


class InvalidContextError(ContextBuilderError):
    """Raised when retrieval or memory context cannot be normalized."""


class ContextRankingError(ContextBuilderError):
    """Raised when semantic context ranking fails."""


class PromptConstructionError(ContextBuilderError):
    """Raised when the final prompt cannot be constructed safely."""


class TokenBudgetExceededError(ContextBuilderError):
    """Raised when context cannot fit inside the configured LLM window."""

