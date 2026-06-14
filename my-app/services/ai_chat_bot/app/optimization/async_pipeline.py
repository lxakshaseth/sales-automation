import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from app.core.logger import log_error, log_event
from app.exceptions.optimization_exceptions import AsyncExecutionError
from app.optimization.concurrency_manager import ConcurrencyManager


class AsyncPipeline:
    """Non-blocking execution pipeline for independent optimization tasks."""

    def __init__(self, *, concurrency_manager: ConcurrencyManager | None = None, timeout_seconds: float = 30.0) -> None:
        self.concurrency_manager = concurrency_manager or ConcurrencyManager()
        self.timeout_seconds = timeout_seconds

    async def run_step(self, name: str, operation: Callable[[], Awaitable[Any]]) -> Any:
        log_event("optimization_async_step_started", step=name)
        try:
            result = await self.concurrency_manager.run(name, asyncio.wait_for(operation(), timeout=self.timeout_seconds))
            log_event("optimization_async_step_completed", step=name)
            return result
        except Exception as exc:
            log_error("Optimization async step failed", step=name, error_type=type(exc).__name__, exc_info=True)
            raise AsyncExecutionError(f"async step failed: {name}") from exc

    async def run_parallel(self, operations: dict[str, Callable[[], Awaitable[Any]]]) -> dict[str, Any]:
        log_event("optimization_async_parallel_started", operation_count=len(operations))
        tasks = {name: asyncio.create_task(self.run_step(name, operation)) for name, operation in operations.items()}
        results: dict[str, Any] = {}
        for name, task in tasks.items():
            results[name] = await task
        log_event("optimization_async_parallel_completed", operation_count=len(results))
        return results

