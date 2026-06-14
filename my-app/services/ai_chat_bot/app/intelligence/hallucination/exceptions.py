class HallucinationGuardError(Exception):
    """Base exception for hallucination reduction failures."""


class SourceVerificationError(HallucinationGuardError):
    """Raised when sources cannot be verified safely."""


class GroundingError(HallucinationGuardError):
    """Raised when response grounding checks fail."""


class FactCheckError(HallucinationGuardError):
    """Raised when fact checking cannot complete safely."""


class ValidationPipelineError(HallucinationGuardError):
    """Raised when the validation pipeline fails."""
