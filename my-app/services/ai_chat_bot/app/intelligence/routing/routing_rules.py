import json
import os
from pathlib import Path
from typing import Any

from app.core.logger import log_error, log_event
from app.intelligence.routing.models import TaskType

DEFAULT_ROUTING_RULES: dict[str, dict[str, Any]] = {
    TaskType.QUICK_REPLY.value: {"provider": "groq", "model_alias": "llama", "strategy": "least_latency"},
    TaskType.REASONING.value: {"provider": "groq", "model_alias": "mixtral", "strategy": "weighted_routing"},
    TaskType.MULTILINGUAL.value: {"provider": "groq", "model_alias": "gemma", "strategy": "weighted_routing"},
    TaskType.TOOL_CALLING.value: {"provider": "groq", "model_alias": "llama", "strategy": "weighted_routing"},
    TaskType.RAG_HEAVY.value: {"provider": "groq", "model_alias": "retrieval_optimized", "strategy": "weighted_routing"},
    TaskType.RETRIEVAL.value: {"provider": "groq", "model_alias": "retrieval_optimized", "strategy": "weighted_routing"},
    TaskType.CLASSIFICATION.value: {"provider": "groq", "model_alias": "lightweight_model", "strategy": "least_cost"},
    TaskType.SUMMARIZATION.value: {"provider": "groq", "model_alias": "llama", "strategy": "weighted_routing"},
    TaskType.CONVERSATION.value: {"provider": "groq", "model_alias": "llama", "strategy": "weighted_routing"},
}


class RoutingRuleEngine:
    """Central routing configuration with JSON/env support and YAML placeholder."""

    def __init__(self, rules: dict[str, dict[str, Any]] | None = None) -> None:
        self.rules = rules or self.load_rules()

    def load_rules(self) -> dict[str, dict[str, Any]]:
        rules = DEFAULT_ROUTING_RULES.copy()
        rules_path = os.getenv("MODEL_ROUTING_RULES_PATH")
        rules_json = os.getenv("MODEL_ROUTING_RULES_JSON")

        try:
            if rules_path:
                file_rules = self._load_rules_file(Path(rules_path))
                rules.update(file_rules)
            if rules_json:
                rules.update(json.loads(rules_json))
        except Exception as exc:
            log_error("Routing rule load failed; using defaults", exc_info=True, error_type=type(exc).__name__)

        self._apply_environment_overrides(rules)
        log_event("routing_rules_loaded", rule_count=len(rules), yaml_supported=False)
        return rules

    def get_rule(self, task_type: str) -> dict[str, Any]:
        return self.rules.get(task_type, self.rules[TaskType.CONVERSATION.value])

    def list_rules(self) -> dict[str, dict[str, Any]]:
        return dict(self.rules)

    def _load_rules_file(self, path: Path) -> dict[str, dict[str, Any]]:
        suffix = path.suffix.lower()
        if suffix == ".json":
            return json.loads(path.read_text(encoding="utf-8"))
        if suffix in {".yaml", ".yml"}:
            log_event("routing_yaml_placeholder", path=str(path))
            raise ValueError("YAML routing files are reserved for future support")
        raise ValueError(f"Unsupported routing rules file type: {suffix}")

    def _apply_environment_overrides(self, rules: dict[str, dict[str, Any]]) -> None:
        for task_type in list(rules):
            env_prefix = f"MODEL_ROUTE_{task_type.upper().replace('-', '_')}"
            provider = os.getenv(f"{env_prefix}_PROVIDER")
            model_alias = os.getenv(f"{env_prefix}_MODEL_ALIAS")
            strategy = os.getenv(f"{env_prefix}_STRATEGY")
            if provider:
                rules[task_type]["provider"] = provider.strip().lower()
            if model_alias:
                rules[task_type]["model_alias"] = model_alias.strip()
            if strategy:
                rules[task_type]["strategy"] = strategy.strip()
