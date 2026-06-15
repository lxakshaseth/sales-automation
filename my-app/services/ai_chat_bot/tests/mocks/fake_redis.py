import fnmatch
import json
import time
from typing import Any


class FakeRedis:
    """Small async Redis test double with TTL semantics for cache/memory tests."""

    def __init__(self) -> None:
        self._store: dict[str, str] = {}
        self._expires_at: dict[str, float] = {}

    async def get(self, key: str) -> str | None:
        self._expire_if_needed(key)
        return self._store.get(key)

    async def set(self, key: str, value: Any, ex: int | None = None) -> bool:
        self._store[key] = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
        if ex is not None:
            self._expires_at[key] = time.time() + ex
        return True

    async def delete(self, *keys: str) -> int:
        deleted = 0
        for key in keys:
            deleted += int(key in self._store)
            self._store.pop(key, None)
            self._expires_at.pop(key, None)
        return deleted

    async def ttl(self, key: str) -> int:
        self._expire_if_needed(key)
        if key not in self._store:
            return -2
        if key not in self._expires_at:
            return -1
        return max(0, int(self._expires_at[key] - time.time()))

    async def incr(self, key: str) -> int:
        self._expire_if_needed(key)
        value = int(self._store.get(key, "0")) + 1
        self._store[key] = str(value)
        return value

    async def expire(self, key: str, seconds: int) -> bool:
        if key not in self._store:
            return False
        self._expires_at[key] = time.time() + seconds
        return True

    def pipeline(self) -> "FakeRedisPipeline":
        return FakeRedisPipeline(self)

    async def scan_iter(self, match: str, count: int = 200):
        del count
        for key in list(self._store):
            self._expire_if_needed(key)
            if key in self._store and fnmatch.fnmatch(key, match):
                yield key

    async def aclose(self) -> None:
        self._store.clear()
        self._expires_at.clear()

    def _expire_if_needed(self, key: str) -> None:
        expires_at = self._expires_at.get(key)
        if expires_at is not None and expires_at <= time.time():
            self._store.pop(key, None)
            self._expires_at.pop(key, None)


class FakeRedisPipeline:
    def __init__(self, redis: FakeRedis) -> None:
        self.redis = redis
        self.operations: list[tuple[str, tuple[Any, ...]]] = []

    def incr(self, key: str) -> "FakeRedisPipeline":
        self.operations.append(("incr", (key,)))
        return self

    def expire(self, key: str, seconds: int) -> "FakeRedisPipeline":
        self.operations.append(("expire", (key, seconds)))
        return self

    async def execute(self) -> list[Any]:
        results: list[Any] = []
        for name, args in self.operations:
            results.append(await getattr(self.redis, name)(*args))
        self.operations.clear()
        return results

