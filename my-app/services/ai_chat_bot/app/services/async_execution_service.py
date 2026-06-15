from collections.abc import Awaitable, Callable
from typing import Any

from app.optimization.async_pipeline import AsyncPipeline


class AsyncExecutionService:
    """Service facade for non-blocking R10 workflows."""

    def __init__(self, *, pipeline: AsyncPipeline | None = None) -> None:
        self.pipeline = pipeline or AsyncPipeline()

    async def run_step(self, name: str, operation: Callable[[], Awaitable[Any]]) -> Any:
        return await self.pipeline.run_step(name, operation)

    async def run_parallel(self, operations: dict[str, Callable[[], Awaitable[Any]]]) -> dict[str, Any]:
        return await self.pipeline.run_parallel(operations)
