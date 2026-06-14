import time
from typing import Any

from app.core.logger import log_error, log_event
from app.intelligence.routing.exceptions import FallbackExhaustedError, ModelSelectionError, RoutingError
from app.intelligence.routing.fallback_router import FallbackRouter
from app.intelligence.routing.load_balancer import LoadBalancer
from app.intelligence.routing.models import ProviderState, RoutingDecision, RoutingRequest, RoutingResponse, RoutingStrategy, TaskType
from app.intelligence.routing.provider_manager import ProviderManager
from app.intelligence.routing.routing_rules import RoutingRuleEngine


class ModelRouter:
    """Only gateway through which LLM requests should flow."""

    def __init__(
        self,
        provider_manager: ProviderManager | None = None,
        rule_engine: RoutingRuleEngine | None = None,
        load_balancer: LoadBalancer | None = None,
        fallback_router: FallbackRouter | None = None,
    ) -> None:
        self.provider_manager = provider_manager or ProviderManager()
        self.rule_engine = rule_engine or RoutingRuleEngine()
        self.load_balancer = load_balancer or LoadBalancer()
        self.fallback_router = fallback_router or FallbackRouter(self.provider_manager)

    async def route_request(self, request: RoutingRequest | dict[str, Any]) -> RoutingResponse:
        started_at = time.perf_counter()
        routing_request = request if isinstance(request, RoutingRequest) else RoutingRequest(**request)
        try:
            task_type = self.determine_task_type(routing_request)
            decision = await self.select_model(routing_request, task_type)
            log_event(
                "model_routing_decision",
                provider=decision.provider,
                model=decision.model,
                task_type=decision.task_type,
                strategy=decision.strategy.value,
            )

            response, fallback = await self.fallback_router.execute_with_fallback(
                routing_request,
                decision,
                self._call_provider,
            )
            latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
            self.provider_manager.mark_success(fallback.to_provider or decision.provider, latency_ms)
            log_event(
                "model_routing_completed",
                provider=fallback.to_provider or decision.provider,
                model=fallback.to_model or decision.model,
                latency_ms=latency_ms,
                fallback_activated=fallback.activated,
            )
            return RoutingResponse(
                success=True,
                content=response.get("content"),
                provider=fallback.to_provider or decision.provider,
                model=fallback.to_model or decision.model,
                decision=decision,
                fallback=fallback,
                latency_ms=latency_ms,
                raw_response=response.get("raw_response", {}),
            )
        except FallbackExhaustedError as exc:
            latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
            log_error("Model routing fallback exhausted", latency_ms=latency_ms, exc_info=True)
            return RoutingResponse(success=False, latency_ms=latency_ms, error="All model providers are temporarily unavailable.", error_type=type(exc).__name__)
        except Exception as exc:
            latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
            log_error("Model routing failed", latency_ms=latency_ms, error_type=type(exc).__name__, exc_info=True)
            return RoutingResponse(success=False, latency_ms=latency_ms, error=str(exc), error_type=type(exc).__name__)

    async def select_model(self, request: RoutingRequest, task_type: str) -> RoutingDecision:
        provider_name = await self.select_provider(request, task_type)
        rule = self.rule_engine.get_rule(task_type)
        model_alias = request.preferred_model or rule.get("model_alias")
        model = self.provider_manager.resolve_model(provider_name, model_alias)
        capability = self.provider_manager.get_model_capability(provider_name, model)

        if request.require_tool_calling and capability and not capability.tool_calling_support:
            raise ModelSelectionError("selected model does not support tool calling")
        if request.require_multilingual and capability and not capability.multilingual_support:
            raise ModelSelectionError("selected model does not support multilingual routing")
        if request.require_retrieval and capability and not capability.retrieval_support:
            raise ModelSelectionError("selected model does not support retrieval-heavy routing")

        status_chain = sorted(
            [self.provider_manager.get_provider_status(name) for name in self.provider_manager.list_providers()],
            key=lambda status: self.provider_manager.configs[status.provider].priority,
        )
        fallback_chain = [status.provider for status in status_chain if status.available and status.provider != provider_name]
        strategy = RoutingStrategy(rule.get("strategy", RoutingStrategy.WEIGHTED_ROUTING.value))

        return RoutingDecision(
            provider=provider_name,
            model=model,
            task_type=task_type,
            strategy=strategy,
            reason=[f"task_rule:{task_type}", f"provider:{provider_name}", f"model_alias:{model_alias}"],
            estimated_latency_score=capability.latency_score if capability else 0.5,
            estimated_cost_score=capability.cost_score if capability else 0.5,
            fallback_chain=fallback_chain,
        )

    async def select_provider(self, request: RoutingRequest, task_type: str) -> str:
        if request.preferred_provider:
            status = self.provider_manager.get_provider_status(request.preferred_provider)
            if status.available:
                return status.provider
            raise RoutingError(f"preferred provider is unavailable: {request.preferred_provider}")

        rule = self.rule_engine.get_rule(task_type)
        preferred = str(rule.get("provider", "")).lower()
        preferred_status = self.provider_manager.get_provider_status(preferred) if preferred else None
        if preferred_status and preferred_status.available and preferred_status.health.status != ProviderState.FAILED:
            return preferred_status.provider

        strategy = RoutingStrategy(rule.get("strategy", RoutingStrategy.WEIGHTED_ROUTING.value))
        statuses = []
        for provider_name in self.provider_manager.list_providers():
            await self.provider_manager.check_provider_health(provider_name)
            statuses.append(self.provider_manager.get_provider_status(provider_name))
        selected = self.load_balancer.select_provider(statuses, strategy=strategy)
        if selected is None:
            raise RoutingError("no available model provider")
        return selected.provider

    def determine_task_type(self, request: RoutingRequest) -> str:
        if request.task_type:
            return str(request.task_type)
        text = f"{request.prompt or ''} {' '.join(message.get('content', '') for message in request.messages)}".lower()
        if request.require_tool_calling or "tool" in text or "function" in text:
            return TaskType.TOOL_CALLING.value
        if request.require_retrieval or "retrieve" in text or "context" in text or "rag" in text:
            return TaskType.RETRIEVAL.value
        if request.require_multilingual or "translate" in text or "language" in text:
            return TaskType.MULTILINGUAL.value
        if "summarize" in text or "summary" in text:
            return TaskType.SUMMARIZATION.value
        if "classify" in text or "category" in text:
            return TaskType.CLASSIFICATION.value
        if "why" in text or "reason" in text or "analyze" in text:
            return TaskType.REASONING.value
        if len(text) < 160:
            return TaskType.QUICK_REPLY.value
        return TaskType.CONVERSATION.value

    async def _call_provider(self, provider_name: str, model: str, request: RoutingRequest) -> dict[str, Any]:
        provider = self.provider_manager.get_provider(provider_name)
        config = self.provider_manager.configs[provider_name]
        if not self.provider_manager.validate_provider(provider_name):
            raise RoutingError(f"provider is not valid for routing: {provider_name}")
        log_event("model_provider_selected", provider=provider_name, model=model, timeout_seconds=request.timeout_seconds or config.timeout_seconds)
        return await provider.generate(request, model)


async def route_request(request: RoutingRequest | dict[str, Any]) -> RoutingResponse:
    return await ModelRouter().route_request(request)
