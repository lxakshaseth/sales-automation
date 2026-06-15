from app.core.logger import log_event
from app.intelligence.routing.models import ProviderStatus, RoutingStrategy


class LoadBalancer:
    """Future-ready provider distribution engine."""

    def __init__(self) -> None:
        self._round_robin_index = 0

    def select_provider(self, statuses: list[ProviderStatus], strategy: RoutingStrategy = RoutingStrategy.WEIGHTED_ROUTING) -> ProviderStatus | None:
        available = [status for status in statuses if status.available]
        if not available:
            return None

        if strategy == RoutingStrategy.ROUND_ROBIN:
            selected = available[self._round_robin_index % len(available)]
            self._round_robin_index += 1
        elif strategy == RoutingStrategy.LEAST_LATENCY:
            selected = min(available, key=lambda item: item.health.average_latency_ms or 0.0)
        elif strategy == RoutingStrategy.LEAST_COST:
            selected = min(available, key=lambda item: item.health.failure_rate)
        else:
            selected = sorted(
                available,
                key=lambda item: (
                    item.health.status.value != "HEALTHY",
                    item.health.failure_rate,
                    item.health.average_latency_ms,
                ),
            )[0]

        log_event("load_balancer_selected_provider", provider=selected.provider, strategy=strategy.value)
        return selected
