import time
import tracemalloc
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.logger import log_event

MetricCategory = str
_request_metrics: ContextVar[dict[MetricCategory, float] | None] = ContextVar("request_metrics", default=None)


@dataclass
class OperationTimer:
    category: MetricCategory
    operation: str
    metadata: dict[str, Any] = field(default_factory=dict)

    async def __aenter__(self):
        self.started_at = time.perf_counter()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        duration_ms = round((time.perf_counter() - self.started_at) * 1000, 2)
        add_timing(self.category, duration_ms)
        payload = {
            "operation": self.operation,
            "category": self.category,
            "duration_ms": duration_ms,
            **self.metadata,
        }
        if exc is not None:
            payload["error_type"] = type(exc).__name__
        log_event("performance_operation", **payload)


def add_timing(category: MetricCategory, duration_ms: float) -> None:
    metrics = _request_metrics.get()
    if metrics is not None:
        metrics[category] = round(metrics.get(category, 0.0) + duration_ms, 2)


@asynccontextmanager
async def measure(category: MetricCategory, operation: str, **metadata: Any):
    async with OperationTimer(category=category, operation=operation, metadata=metadata):
        yield


async def timed(category: MetricCategory, operation: str, func: Callable[[], Awaitable[Any]], **metadata: Any) -> Any:
    async with measure(category, operation, **metadata):
        return await func()


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Collect coarse request timings plus per-category timings recorded by services."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if not tracemalloc.is_tracing():
            tracemalloc.start()
        token = _request_metrics.set({})
        started_at = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            total_ms = round((time.perf_counter() - started_at) * 1000, 2)
            current_bytes, peak_bytes = tracemalloc.get_traced_memory()
            metrics = _request_metrics.get() or {}
            log_event(
                "http_performance",
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                total_latency_ms=total_ms,
                db_latency_ms=metrics.get("db", 0.0),
                redis_latency_ms=metrics.get("redis", 0.0),
                ai_latency_ms=metrics.get("ai", 0.0),
                embedding_latency_ms=metrics.get("embedding", 0.0),
                retrieval_latency_ms=metrics.get("retrieval", 0.0),
                serialization_latency_ms=metrics.get("serialization", 0.0),
                middleware_latency_ms=metrics.get("middleware", 0.0),
                cache_latency_ms=metrics.get("cache", 0.0),
                memory_current_kb=round(current_bytes / 1024, 2),
                memory_peak_kb=round(peak_bytes / 1024, 2),
            )
            _request_metrics.reset(token)
