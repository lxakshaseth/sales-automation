import time
from collections.abc import Awaitable, Callable
from typing import Generic, TypeVar


T = TypeVar("T")


class TTLCache(Generic[T]):
    """Small in-process TTL cache used as a fast fallback around remote stores."""

    def __init__(self, ttl_seconds: int, max_entries: int = 512) -> None:
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._items: dict[str, tuple[float, T]] = {}

    def get(self, key: str) -> T | None:
        item = self._items.get(key)
        if item is None:
            return None
        expires_at, value = item
        if expires_at < time.time():
            self._items.pop(key, None)
            return None
        return value

    def set(self, key: str, value: T, ttl_seconds: int | None = None) -> None:
        if len(self._items) >= self.max_entries:
            self._items.pop(next(iter(self._items)))
        self._items[key] = (time.time() + (ttl_seconds or self.ttl_seconds), value)

    def invalidate_prefix(self, prefix: str) -> None:
        for key in [item for item in self._items if item.startswith(prefix)]:
            self._items.pop(key, None)


async def get_or_set(cache: TTLCache[T], key: str, factory: Callable[[], Awaitable[T]], ttl_seconds: int | None = None) -> T:
    cached = cache.get(key)
    if cached is not None:
        return cached
    value = await factory()
    cache.set(key, value, ttl_seconds=ttl_seconds)
    return value
