from collections.abc import Awaitable, Callable
from typing import Any

from app.models.batch_models import BatchRequest, BatchResult
from app.optimization.batch_processor import BatchProcessor


class BatchingService:
    """Service facade for R10 batch execution."""

    def __init__(self, *, processor: BatchProcessor | None = None) -> None:
        self.processor = processor or BatchProcessor()

    async def process_batch(self, request: BatchRequest, handler: Callable[[Any], Awaitable[Any]]) -> BatchResult:
        return await self.processor.process(request, handler)

