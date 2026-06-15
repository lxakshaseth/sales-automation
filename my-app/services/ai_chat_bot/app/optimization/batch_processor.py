import time
from collections.abc import Awaitable, Callable
from typing import Any

from app.core.logger import log_error, log_event
from app.exceptions.optimization_exceptions import BatchProcessingError
from app.models.batch_models import BatchItemResult, BatchRequest, BatchResult
from app.utils.async_helpers import gather_limited


class BatchProcessor:
    """Memory-safe async batching for embeddings, retrieval, and memory operations."""

    def __init__(self, *, max_concurrency: int = 5) -> None:
        self.max_concurrency = max(1, max_concurrency)

    async def process(self, request: BatchRequest, handler: Callable[[Any], Awaitable[Any]]) -> BatchResult:
        started = time.perf_counter()
        log_event("optimization_batch_started", batch_id=request.batch_id, batch_type=request.batch_type, total_items=len(request.items))
        try:
            item_results: list[BatchItemResult] = []
            for offset in range(0, len(request.items), request.batch_size):
                chunk = request.items[offset : offset + request.batch_size]
                coroutines = [self._handle_item(offset + index, item, handler) for index, item in enumerate(chunk)]
                item_results.extend(await gather_limited(self.max_concurrency, coroutines))
            success_count = sum(1 for item in item_results if item.success)
            failed_count = len(item_results) - success_count
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            log_event("optimization_batch_completed", batch_id=request.batch_id, successful_items=success_count, failed_items=failed_count, duration_ms=duration_ms)
            return BatchResult(
                batch_id=request.batch_id,
                batch_type=request.batch_type,
                success=failed_count == 0,
                results=item_results,
                total_items=len(request.items),
                successful_items=success_count,
                failed_items=failed_count,
                duration_ms=duration_ms,
            )
        except Exception as exc:
            log_error("Optimization batch failed", batch_id=request.batch_id, error_type=type(exc).__name__, exc_info=True)
            raise BatchProcessingError("batch processing failed") from exc

    async def _handle_item(self, index: int, item: Any, handler: Callable[[Any], Awaitable[Any]]) -> BatchItemResult:
        try:
            return BatchItemResult(index=index, success=True, value=await handler(item))
        except Exception as exc:
            return BatchItemResult(index=index, success=False, error={"type": type(exc).__name__, "message": str(exc)})

