import os
import time
from typing import Any, Protocol

from groq import AsyncGroq

from app.core.logger import log_error, log_event
from app.intelligence.routing.exceptions import (
    ProviderConfigurationError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from app.intelligence.routing.models import ModelCapability, ProviderConfig, ProviderHealth, ProviderState, ProviderStatus, RoutingRequest


class LLMProvider(Protocol):
    config: ProviderConfig

    async def generate(self, request: RoutingRequest, model: str) -> dict[str, Any]:
        ...


class PlaceholderProvider:
    def __init__(self, config: ProviderConfig) -> None:
        self.config = config

    async def generate(self, request: RoutingRequest, model: str) -> dict[str, Any]:
        raise ProviderUnavailableError(f"{self.config.name} provider adapter is not active")


class GroqProvider:
    def __init__(self, config: ProviderConfig) -> None:
        self.config = config
        self._client: AsyncGroq | None = None

    def _client_or_raise(self) -> AsyncGroq:
        if not self.config.api_key:
            raise ProviderConfigurationError("GROQ_API_KEY is not configured")
        if self._client is None:
            self._client = AsyncGroq(api_key=self.config.api_key)
        return self._client

    async def generate(self, request: RoutingRequest, model: str) -> dict[str, Any]:
        messages = request.messages or [{"role": "user", "content": request.prompt or ""}]
        response = await self._client_or_raise().chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.4 if request.temperature is None else request.temperature,
            max_tokens=request.max_tokens,
        )
        content = response.choices[0].message.content
        if not content:
            raise ProviderUnavailableError("provider returned empty response")
        return {"content": content.strip(), "raw_response": response.model_dump() if hasattr(response, "model_dump") else {}}


class ProviderManager:
    """Registers providers, validates configuration, and tracks provider health."""

    def __init__(self) -> None:
        self.providers: dict[str, LLMProvider] = {}
        self.configs: dict[str, ProviderConfig] = {}
        self.health: dict[str, ProviderHealth] = {}
        self.capabilities: dict[tuple[str, str], ModelCapability] = {}
        self._register_default_providers()

    def register_provider(self, config: ProviderConfig, provider: LLMProvider | None = None) -> None:
        resolved_provider: LLMProvider
        if provider is not None:
            resolved_provider = provider
        elif config.name == "groq":
            resolved_provider = GroqProvider(config)
        else:
            resolved_provider = PlaceholderProvider(config)

        self.configs[config.name] = config
        self.providers[config.name] = resolved_provider
        self.health.setdefault(
            config.name,
            ProviderHealth(status=ProviderState.HEALTHY if config.enabled and self.validate_provider(config.name) else ProviderState.DISABLED),
        )
        self._register_model_capabilities(config)
        log_event("provider_registered", provider=config.name, enabled=config.enabled, priority=config.priority)

    def get_provider(self, provider_name: str) -> LLMProvider:
        normalized = provider_name.strip().lower()
        provider = self.providers.get(normalized)
        if provider is None:
            raise ProviderUnavailableError(f"provider is not registered: {normalized}")
        return provider

    def list_providers(self) -> list[str]:
        return sorted(self.providers)

    def validate_provider(self, provider_name: str) -> bool:
        config = self.configs.get(provider_name.strip().lower())
        if config is None or not config.enabled:
            return False
        if config.api_key_env and not config.api_key and config.name != "ollama":
            return False
        if not config.model_aliases and not config.default_model:
            return False
        return True

    async def check_provider_health(self, provider_name: str) -> ProviderHealth:
        normalized = provider_name.strip().lower()
        config = self.configs.get(normalized)
        current = self.health.get(normalized, ProviderHealth())
        if config is None or not config.enabled:
            current.status = ProviderState.DISABLED
        elif current.cooldown_until_epoch and current.cooldown_until_epoch > time.time():
            current.status = ProviderState.DEGRADED
        elif not self.validate_provider(normalized):
            current.status = ProviderState.FAILED
        elif current.failure_rate >= 0.50 or current.consecutive_failures >= 3:
            current.status = ProviderState.FAILED
        elif current.failure_rate >= 0.20 or current.timeout_rate >= 0.20:
            current.status = ProviderState.DEGRADED
        else:
            current.status = ProviderState.HEALTHY

        self.health[normalized] = current
        log_event("provider_health_checked", provider=normalized, status=current.status.value)
        return current

    def get_provider_status(self, provider_name: str) -> ProviderStatus:
        normalized = provider_name.strip().lower()
        config = self.configs.get(normalized)
        health = self.health.get(normalized, ProviderHealth())
        configured = config is not None and self.validate_provider(normalized)
        available = configured and health.status in {ProviderState.HEALTHY, ProviderState.DEGRADED}
        return ProviderStatus(
            provider=normalized,
            available=available,
            configured=configured,
            health=health,
            enabled=bool(config and config.enabled),
            active_model_count=len(config.model_aliases) if config else 0,
        )

    def resolve_model(self, provider_name: str, model_or_alias: str | None) -> str:
        config = self.configs.get(provider_name.strip().lower())
        if config is None:
            raise ProviderUnavailableError(f"provider is not registered: {provider_name}")
        if model_or_alias and model_or_alias in config.model_aliases:
            return config.model_aliases[model_or_alias]
        if model_or_alias:
            return model_or_alias
        if config.default_model:
            return config.default_model
        raise ProviderConfigurationError(f"default model is not configured for provider: {provider_name}")

    def get_model_capability(self, provider_name: str, model: str) -> ModelCapability | None:
        return self.capabilities.get((provider_name.strip().lower(), model))

    def mark_success(self, provider_name: str, latency_ms: float) -> None:
        health = self.health.setdefault(provider_name, ProviderHealth())
        previous_volume = health.request_volume
        health.request_volume += 1
        health.average_latency_ms = ((health.average_latency_ms * previous_volume) + latency_ms) / health.request_volume
        health.consecutive_failures = 0
        health.status = ProviderState.HEALTHY

    def mark_failure(self, provider_name: str, error: Exception, *, timeout: bool = False, rate_limited: bool = False) -> None:
        config = self.configs.get(provider_name)
        health = self.health.setdefault(provider_name, ProviderHealth())
        health.request_volume += 1
        health.consecutive_failures += 1
        health.failure_rate = min(1.0, (health.failure_rate + 1.0 / max(health.request_volume, 1)) / 2)
        if timeout:
            health.timeout_rate = min(1.0, (health.timeout_rate + 1.0 / max(health.request_volume, 1)) / 2)
        if rate_limited and config:
            health.cooldown_until_epoch = time.time() + config.cooldown_seconds
        health.last_error = str(error)
        health.status = ProviderState.DEGRADED if health.consecutive_failures < 3 else ProviderState.FAILED

    def classify_provider_error(self, exc: Exception) -> Exception:
        text = str(exc).lower()
        if "429" in text or "rate limit" in text or "too many requests" in text:
            return ProviderRateLimitError(str(exc))
        if "timeout" in text or "timed out" in text:
            return ProviderTimeoutError(str(exc))
        return exc

    def _register_default_providers(self) -> None:
        timeout = float(os.getenv("PROVIDER_TIMEOUT", "30"))
        retry_limit = int(os.getenv("MODEL_ROUTER_RETRY_LIMIT", "2"))
        cooldown = float(os.getenv("PROVIDER_COOLDOWN_SECONDS", "60"))
        providers = ["groq", "openai", "gemini", "ollama", "claude", "mistral"]
        env_prefixes = {
            "groq": "GROQ",
            "openai": "OPENAI",
            "claude": "CLAUDE",
            "gemini": "GEMINI",
            "mistral": "MISTRAL",
            "ollama": "OLLAMA",
        }
        for index, name in enumerate(providers, start=1):
            prefix = env_prefixes[name]
            api_key_env = f"{prefix}_API_KEY"
            enabled = os.getenv(f"{prefix}_ENABLED", "true" if name == "groq" else "false").lower() in {"1", "true", "yes", "on"}
            aliases = self._load_model_aliases(prefix)
            default_model = os.getenv(f"{prefix}_DEFAULT_MODEL") or os.getenv(f"{prefix}_MODEL")
            self.register_provider(
                ProviderConfig(
                    name=name,
                    enabled=enabled,
                    api_key_env=api_key_env,
                    api_key=os.getenv(api_key_env),
                    base_url_env=f"{prefix}_BASE_URL",
                    base_url=os.getenv(f"{prefix}_BASE_URL"),
                    default_model=default_model,
                    model_aliases=aliases,
                    priority=int(os.getenv(f"{prefix}_PRIORITY", str(index))),
                    timeout_seconds=float(os.getenv(f"{prefix}_TIMEOUT", str(timeout))),
                    retry_limit=int(os.getenv(f"{prefix}_RETRY_LIMIT", str(retry_limit))),
                    cooldown_seconds=float(os.getenv(f"{prefix}_COOLDOWN_SECONDS", str(cooldown))),
                    weight=float(os.getenv(f"{prefix}_ROUTING_WEIGHT", "1")),
                )
            )

    def _load_model_aliases(self, prefix: str) -> dict[str, str]:
        aliases: dict[str, str] = {}
        raw_json = os.getenv(f"{prefix}_MODEL_ALIASES_JSON")
        if raw_json:
            try:
                aliases.update({str(key): str(value) for key, value in dict(__import__("json").loads(raw_json)).items()})
            except Exception as exc:
                log_error("Provider model alias JSON invalid", provider_prefix=prefix, exc_info=True, error_type=type(exc).__name__)

        alias_names = ["llama", "mixtral", "gemma", "retrieval_optimized", "lightweight_model"]
        for alias in alias_names:
            env_name = f"{prefix}_MODEL_{alias.upper()}"
            if os.getenv(env_name):
                aliases[alias] = os.getenv(env_name, "").strip()

        default_model = os.getenv(f"{prefix}_MODEL") or os.getenv(f"{prefix}_DEFAULT_MODEL")
        if default_model:
            for alias in alias_names:
                aliases.setdefault(alias, default_model)
        return aliases

    def _register_model_capabilities(self, config: ProviderConfig) -> None:
        for alias, model in config.model_aliases.items():
            self.capabilities[(config.name, model)] = ModelCapability(
                model=model,
                provider=config.name,
                multilingual_support=alias in {"gemma", "llama", "mixtral"},
                tool_calling_support=alias in {"llama", "mixtral"},
                retrieval_support=alias == "retrieval_optimized",
                reasoning_score=0.85 if alias == "mixtral" else 0.65,
                latency_score=0.85 if alias in {"llama", "lightweight_model"} else 0.65,
                cost_score=0.90 if alias == "lightweight_model" else 0.70,
                quality_score=0.85 if alias in {"mixtral", "retrieval_optimized"} else 0.75,
                metadata={"alias": alias},
            )
