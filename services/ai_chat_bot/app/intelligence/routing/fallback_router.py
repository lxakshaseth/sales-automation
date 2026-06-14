import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from app.core.logger import log_error, log_event
from app.intelligence.routing.exceptions import FallbackExhaustedError, ProviderRateLimitError, ProviderTimeoutError
from app.intelligence.routing.models import FallbackDecision, RoutingDecision, RoutingRequest
from app.intelligence.routing.provider_manager import ProviderManager

ProviderCall = Callable[[str, str, RoutingRequest], Awaitable[dict[str, Any]]]


class FallbackRouter:
    """Retries failed providers and gracefully shifts to fallback providers/models."""

    def __init__(self, provider_manager: ProviderManager) -> None:
        self.provider_manager = provider_manager

    async def execute_with_fallback(
        self,
        request: RoutingRequest,
        decision: RoutingDecision,
        provider_call: ProviderCall,
    ) -> tuple[dict[str, Any], FallbackDecision]:
        chain = [decision.provider, *[provider for provider in decision.fallback_chain if provider != decision.provider]]
        last_error: Exception | None = None
        fallback_decision = FallbackDecision(activated=False, from_provider=decision.provider, from_model=decision.model)

        for provider_name in chain:
            config = self.provider_manager.configs[provider_name]
            model = decision.model if provider_name == decision.provider else self.provider_manager.resolve_model(provider_name, None)
            retry_limit = config.retry_limit

            for attempt in range(retry_limit + 1):
                try:
                    if attempt > 0:
                        log_event("model_router_retry_attempt", provider=provider_name, model=model, attempt=attempt)
                        await asyncio.sleep(min(2**attempt * 0.25, 3.0))
                    response = await asyncio.wait_for(provider_call(provider_name, model, request), timeout=request.timeout_seconds or config.timeout_seconds)
                    fallback_decision = FallbackDecision(
                        activated=provider_name != decision.provider or attempt > 0,
                        from_provider=decision.provider,
                        from_model=decision.model,
                        to_provider=provider_name,
                        to_model=model,
                        attempt=attempt,
                        reason="provider_recovered" if provider_name == decision.provider and attempt > 0 else None,
                    )
                    return response, fallback_decision
                except TimeoutError as exc:
                    last_error = ProviderTimeoutError(str(exc) or "provider timeout")
                    self.provider_manager.mark_failure(provider_name, last_error, timeout=True)
                    log_error("Model provider timeout", provider=provider_name, model=model, attempt=attempt, exc_info=True)
                except Exception as exc:
                    classified = self.provider_manager.classify_provider_error(exc)
                    last_error = classified
                    self.provider_manager.mark_failure(provider_name, classified, rate_limited=isinstance(classified, ProviderRateLimitError))
                    if isinstance(classified, ProviderRateLimitError):
                        log_error("Model provider rate limited", provider=provider_name, model=model, attempt=attempt, exc_info=True)
                    else:
                        log_error("Model provider failure", provider=provider_name, model=model, attempt=attempt, error_type=type(classified).__name__, exc_info=True)

            log_event("fallback_router_activated", failed_provider=provider_name, next_candidates=[candidate for candidate in chain if candidate != provider_name])

        raise FallbackExhaustedError(str(last_error) if last_error else "fallback providers exhausted")
