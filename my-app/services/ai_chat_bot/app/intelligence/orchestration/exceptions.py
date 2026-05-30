class OrchestrationError(Exception):
    """Base exception for AI orchestration failures."""


class WorkflowExecutionError(OrchestrationError):
    """Raised when a workflow step fails after recovery attempts."""


class OrchestrationTimeoutError(OrchestrationError):
    """Raised when workflow execution exceeds configured timeout."""


class ContextBuildError(OrchestrationError):
    """Raised when orchestration context cannot be built safely."""


class DecisionError(OrchestrationError):
    """Raised when orchestration decisions cannot be made safely."""
