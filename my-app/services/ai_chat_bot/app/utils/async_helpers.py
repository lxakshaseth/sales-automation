import asyncio
from collections.abc import Awaitable
from typing import TypeVar


T = TypeVar("T")


async def gather_limited(limit: int, coroutines: list[Awaitable[T]]) -> list[T]:
    semaphore = asyncio.Semaphore(max(1, limit))

    async def run(coro: Awaitable[T]) -> T:
        async with semaphore:
            return await coro

    return await asyncio.gather(*(run(coro) for coro in coroutines))


async def run_with_timeout(coro: Awaitable[T], timeout_seconds: float) -> T:
    return await asyncio.wait_for(coro, timeout=timeout_seconds)

