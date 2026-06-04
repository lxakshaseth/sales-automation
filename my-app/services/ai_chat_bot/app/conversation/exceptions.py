class ConversationError(Exception):
    """Base error for conversation layer failures."""


class IntentDetectionError(ConversationError):
    """Raised when intent detection cannot complete."""
