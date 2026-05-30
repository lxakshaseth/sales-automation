class ConfidenceError(Exception):
    """Base exception for confidence scoring failures."""


class ConfidenceInputError(ConfidenceError):
    """Raised when confidence scoring receives malformed inputs."""


class ConfidenceCalculationError(ConfidenceError):
    """Raised when a confidence component cannot be calculated safely."""
