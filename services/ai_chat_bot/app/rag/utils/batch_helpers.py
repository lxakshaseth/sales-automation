from collections.abc import Iterable
from typing import TypeVar

T = TypeVar("T")


def batched(items: Iterable[T], batch_size: int) -> Iterable[list[T]]:
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")

    batch: list[T] = []
    for item in items:
        batch.append(item)
        if len(batch) >= batch_size:
            yield batch
            batch = []

    if batch:
        yield batch

