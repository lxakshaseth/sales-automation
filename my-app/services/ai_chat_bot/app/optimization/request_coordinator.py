from collections.abc import Awaitable, Callable
from typing import Any

from app.core.logger import log_event
from app.models.optimization_models import OptimizationConfig, OptimizationResult
from app.optimization.async_pipeline import AsyncPipeline
from app.optimization.performance_monitor import PerformanceMonitor


class RequestCoordinator:
    """Coordinate cache-aware async request flows without implementing business logic."""

    def __init__(
        self,
        *,
        config: OptimizationConfig | None = None,
        async_pipeline: AsyncPipeline | None = None,
        performance_monitor: PerformanceMonitor | None = None,
    ) -> None:
        self.config = config or OptimizationConfig()
        self.async_pipeline = async_pipeline or AsyncPipeline(timeout_seconds=self.config.request_timeout_seconds)
        self.performance_monitor = performance_monitor or PerformanceMonitor()

    async def coordinate(self, operation_name: str, operation: Callable[[], Awaitable[Any]]) -> OptimizationResult:
        result = None
        duration_ms = 0.0
        async with self.performance_monitor.track(operation_name) as metrics:
            log_event("optimization_request_started", operation_name=operation_name)
            result = await self.async_pipeline.run_step(operation_name, operation)
            metrics.success = True
            log_event("optimization_request_completed", operation_name=operation_name)
        snapshot = self.performance_monitor.snapshot()
        if snapshot.metrics:
            duration_ms = snapshot.metrics[-1].duration_ms
        return OptimizationResult(success=True, operation=operation_name, result=result, duration_ms=duration_ms)
