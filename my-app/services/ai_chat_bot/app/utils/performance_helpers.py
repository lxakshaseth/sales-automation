import time
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator


def now_ms() -> float:
    return time.perf_counter() * 1000


@asynccontextmanager
async def measure_duration() -> AsyncIterator[dict[str, float]]:
    state = {"started_ms": now_ms(), "duration_ms": 0.0}
    try:
        yield state
    finally:
        state["duration_ms"] = round(now_ms() - state["started_ms"], 2)

