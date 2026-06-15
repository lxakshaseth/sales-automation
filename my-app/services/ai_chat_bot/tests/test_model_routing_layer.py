import asyncio

from app.intelligence.routing import ModelRouter, ProviderManager
from app.intelligence.routing.exceptions import ProviderRateLimitError
from app.intelligence.routing.load_balancer import LoadBalancer
from app.intelligence.routing.models import ProviderConfig, ProviderHealth, ProviderState, ProviderStatus, RoutingRequest, RoutingStrategy
from app.intelligence.routing.routing_rules import RoutingRuleEngine


class FakeProvider:
    def __init__(self, config: ProviderConfig, failures_before_success: int = 0) -> None:
        self.config = config
        self.failures_before_success = failures_before_success
        self.calls = 0

    async def generate(self, request: RoutingRequest, model: str) -> dict:
        self.calls += 1
        if self.calls <= self.failures_before_success:
            raise ProviderRateLimitError("429 rate limit")
        return {"content": f"{self.config.name}:{model}", "raw_response": {"ok": True}}


def build_provider_manager() -> ProviderManager:
    manager = ProviderManager()
    manager.providers.clear()
    manager.configs.clear()
    manager.health.clear()
    manager.capabilities.clear()

    groq = ProviderConfig(
        name="groq",
        enabled=True,
        api_key="test-key",
        model_aliases={
            "llama": "groq-llama-env",
            "mixtral": "groq-mixtral-env",
            "retrieval_optimized": "groq-rag-env",
            "lightweight_model": "groq-small-env",
        },
        default_model="groq-llama-env",
        priority=1,
        retry_limit=0,
    )
    openai = ProviderConfig(
        name="openai",
        enabled=True,
        api_key="test-key",
        model_aliases={"llama": "openai-llama-env"},
        default_model="openai-llama-env",
        priority=2,
        retry_limit=0,
    )
    manager.register_provider(groq, FakeProvider(groq))
    manager.register_provider(openai, FakeProvider(openai))
    return manager


def test_router_selects_rule_configured_model_alias():
    async def run():
        manager = build_provider_manager()
        router = ModelRouter(provider_manager=manager, rule_engine=RoutingRuleEngine())
        response = await router.route_request({"prompt": "Please analyze why the lead is likely to convert.", "task_type": "reasoning"})
        return response

    response = asyncio.run(run())

    assert response.success is True
    assert response.provider == "groq"
    assert response.model == "groq-mixtral-env"
    assert response.decision is not None
    assert response.decision.task_type == "reasoning"


def test_router_falls_back_after_provider_failure():
    async def run():
        manager = build_provider_manager()
        groq_config = manager.configs["groq"]
        manager.register_provider(groq_config, FakeProvider(groq_config, failures_before_success=1))
        router = ModelRouter(provider_manager=manager, rule_engine=RoutingRuleEngine())
        return await router.route_request({"prompt": "Hi", "task_type": "quick_reply"})

    response = asyncio.run(run())

    assert response.success is True
    assert response.provider == "openai"
    assert response.fallback is not None
    assert response.fallback.activated is True
    assert response.fallback.from_provider == "groq"
    assert response.fallback.to_provider == "openai"


def test_provider_manager_marks_rate_limit_cooldown():
    manager = build_provider_manager()

    manager.mark_failure("groq", ProviderRateLimitError("429 rate limit"), rate_limited=True)
    status = manager.get_provider_status("groq")

    assert status.health.cooldown_until_epoch is not None
    assert status.health.status == ProviderState.DEGRADED


def test_load_balancer_selects_least_latency_provider():
    balancer = LoadBalancer()
    selected = balancer.select_provider(
        [
            ProviderStatus(
                provider="groq",
                available=True,
                configured=True,
                enabled=True,
                health=ProviderHealth(status=ProviderState.HEALTHY, average_latency_ms=80),
            ),
            ProviderStatus(
                provider="openai",
                available=True,
                configured=True,
                enabled=True,
                health=ProviderHealth(status=ProviderState.HEALTHY, average_latency_ms=40),
            ),
        ],
        strategy=RoutingStrategy.LEAST_LATENCY,
    )

    assert selected is not None
    assert selected.provider == "openai"
