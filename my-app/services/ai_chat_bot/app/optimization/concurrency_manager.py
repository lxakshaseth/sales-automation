import asyncio
from collections.abc import Awaitable
from typing import TypeVar

from app.core.logger import log_event

T = TypeVar("T")


class ConcurrencyManager:
    """Bound async concurrency to protect Groq, Redis, vector search, and workers."""

    def __init__(self, *, max_concurrency: int = 20) -> None:
        self.max_concurrency = max(1, max_concurrency)
        self._semaphore = asyncio.Semaphore(self.max_concurrency)
        self.active_requests = 0

    async def run(self, operation_name: str, coro: Awaitable[T]) -> T:
        async with self._semaphore:
            self.active_requests += 1
            log_event("optimization_concurrency_acquired", operation_name=operation_name, active_requests=self.active_requests)
            try:
                return await coro
            finally:
                self.active_requests = max(0, self.active_requests - 1)
                log_event("optimization_concurrency_released", operation_name=operation_name, active_requests=self.active_requests)

