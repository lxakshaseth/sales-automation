class RoutingError(Exception):
    """Base exception for model routing failures."""


class ProviderConfigurationError(RoutingError):
    """Raised when provider configuration is missing or invalid."""


class ProviderUnavailableError(RoutingError):
    """Raised when a provider cannot currently serve traffic."""


class ModelSelectionError(RoutingError):
    """Raised when no valid model can satisfy a routing request."""


class ProviderRateLimitError(ProviderUnavailableError):
    """Raised when provider rate limits require failover or cooldown."""


class ProviderTimeoutError(ProviderUnavailableError):
    """Raised when provider execution exceeds configured timeouts."""


class FallbackExhaustedError(RoutingError):
    """Raised when all fallback providers and models are exhausted."""
