class EvaluationError(Exception):
    """Base exception for evaluation framework failures."""


class BenchmarkDatasetError(EvaluationError):
    """Raised when benchmark datasets are missing or malformed."""


class BenchmarkExecutionError(EvaluationError):
    """Raised when a benchmark cannot execute safely."""


class ScoringError(EvaluationError):
    """Raised when scoring cannot be completed safely."""


class RegressionError(EvaluationError):
    """Raised when regression comparison fails."""
