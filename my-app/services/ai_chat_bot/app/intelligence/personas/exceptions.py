class PersonaError(Exception):
    """Base exception for persona system failures."""


class PersonaConfigurationError(PersonaError):
    """Raised when a persona is missing or invalid."""


class PersonaValidationError(PersonaError):
    """Raised when persona output violates safety rules."""


class LanguageAdaptationError(PersonaError):
    """Raised when language adaptation cannot be completed safely."""
