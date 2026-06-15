import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from app.core.logger import log_event
from app.models.performance_models import PerformanceMetrics, PerformanceSnapshot


class PerformanceMonitor:
    """In-process metrics collector with future Prometheus/Grafana handoff points."""

    def __init__(self, *, max_samples: int = 1000) -> None:
        self.max_samples = max(1, max_samples)
        self._metrics: list[PerformanceMetrics] = []

    @asynccontextmanager
    async def track(self, operation_name: str, **metadata) -> AsyncIterator[PerformanceMetrics]:
        started = time.perf_counter()
        metrics = PerformanceMetrics(operation_name=operation_name, metadata=metadata)
        try:
            yield metrics
        except Exception:
            metrics.success = False
            raise
        finally:
            metrics.duration_ms = round((time.perf_counter() - started) * 1000, 2)
            self.record(metrics)
            log_event("optimization_performance_recorded", operation_name=operation_name, duration_ms=metrics.duration_ms, success=metrics.success)

    def record(self, metrics: PerformanceMetrics) -> None:
        self._metrics.append(metrics)
        if len(self._metrics) > self.max_samples:
            self._metrics = self._metrics[-self.max_samples :]

    def snapshot(self) -> PerformanceSnapshot:
        total = len(self._metrics)
        average = sum(item.duration_ms for item in self._metrics) / total if total else 0.0
        hits = sum(item.cache_hits for item in self._metrics)
        misses = sum(item.cache_misses for item in self._metrics)
        hit_rate = hits / (hits + misses) if hits + misses else 0.0
        return PerformanceSnapshot(
            metrics=list(self._metrics),
            total_operations=total,
            average_latency_ms=round(average, 2),
            cache_hit_rate=round(hit_rate, 4),
        )

