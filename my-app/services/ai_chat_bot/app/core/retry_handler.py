import asyncio
import functools
import logging
import random
import time
from dataclasses import dataclass
from typing import Any, Callable, Iterable, TypeVar

from app.core.config import (
    RETRY_BASE_DELAY_SECONDS,
    RETRY_MAX_ATTEMPTS,
    RETRY_MAX_DELAY_SECONDS,
    RETRY_TIMEOUT_SECONDS,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass(frozen=True)
class RetryConfig:
    """Reusable retry policy for external APIs and autonomous worker tasks."""

    max_attempts: int = RETRY_MAX_ATTEMPTS
    base_delay_seconds: float = RETRY_BASE_DELAY_SECONDS
    max_delay_seconds: float = RETRY_MAX_DELAY_SECONDS
    timeout_seconds: float | None = RETRY_TIMEOUT_SECONDS
    exponential_base: float = 2.0
    jitter_seconds: float = 0.1
    retry_exceptions: tuple[type[BaseException], ...] = (Exception,)


class RetryExhaustedError(RuntimeError):
    """Raised after all retry attempts fail."""


def _normalize_config(config: RetryConfig | None, **overrides: Any) -> RetryConfig:
    base = config or RetryConfig()
    values = {
        "max_attempts": max(1, int(overrides.get("max_attempts", base.max_attempts))),
        "base_delay_seconds": max(0.0, float(overrides.get("base_delay_seconds", base.base_delay_seconds))),
        "max_delay_seconds": max(0.0, float(overrides.get("max_delay_seconds", base.max_delay_seconds))),
        "timeout_seconds": overrides.get("timeout_seconds", base.timeout_seconds),
        "exponential_base": max(1.0, float(overrides.get("exponential_base", base.exponential_base))),
        "jitter_seconds": max(0.0, float(overrides.get("jitter_seconds", base.jitter_seconds))),
        "retry_exceptions": overrides.get("retry_exceptions", base.retry_exceptions),
    }
    if values["timeout_seconds"] is not None:
        values["timeout_seconds"] = max(0.1, float(values["timeout_seconds"]))

    retry_exceptions = values["retry_exceptions"]
    if not isinstance(retry_exceptions, tuple):
        retry_exceptions = tuple(retry_exceptions)
    values["retry_exceptions"] = retry_exceptions

    return RetryConfig(**values)


def _delay_for_attempt(config: RetryConfig, attempt: int) -> float:
    exponential_delay = config.base_delay_seconds * (config.exponential_base ** max(0, attempt - 1))
    capped_delay = min(exponential_delay, config.max_delay_seconds)
    if config.jitter_seconds:
        capped_delay += random.uniform(0, config.jitter_seconds)

    return capped_delay


def _should_retry(exc: BaseException, retry_exceptions: Iterable[type[BaseException]]) -> bool:
    return isinstance(exc, tuple(retry_exceptions))


async def _recover_failed_queue_jobs(queue_name: str | None = None) -> dict[str, Any] | None:
    """Delegate failed RQ job recovery to the queue module without import cycles."""
    try:
        from app.queue.worker import recover_failed_jobs

        return await recover_failed_jobs(queue_name=queue_name) if queue_name else await recover_failed_jobs()
    except Exception:
        logger.exception("Failed task recovery hook failed")
        return None


def retry_async(
    func: Callable[..., Any] | None = None,
    *,
    config: RetryConfig | None = None,
    max_attempts: int | None = None,
    base_delay_seconds: float | None = None,
    max_delay_seconds: float | None = None,
    timeout_seconds: float | None = None,
    jitter_seconds: float | None = None,
    retry_exceptions: tuple[type[BaseException], ...] | None = None,
    recover_failed_tasks: bool = False,
    recovery_queue_name: str | None = None,
) -> Callable[..., Any]:
    """
    Async retry decorator with exponential backoff and timeout protection.

    Use this around email, CRM, WhatsApp, calendar, and agent workflow calls that
    can fail transiently due to provider rate limits or network issues.
    """
    overrides = {
        key: value
        for key, value in {
            "max_attempts": max_attempts,
            "base_delay_seconds": base_delay_seconds,
            "max_delay_seconds": max_delay_seconds,
            "timeout_seconds": timeout_seconds,
            "jitter_seconds": jitter_seconds,
            "retry_exceptions": retry_exceptions,
        }.items()
        if value is not None
    }
    retry_config = _normalize_config(config, **overrides)

    def decorator(target: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(target)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_error: BaseException | None = None
            for attempt in range(1, retry_config.max_attempts + 1):
                try:
                    call = target(*args, **kwargs)
                    if retry_config.timeout_seconds is not None:
                        return await asyncio.wait_for(call, timeout=retry_config.timeout_seconds)
                    return await call
                except BaseException as exc:
                    last_error = exc
                    if not _should_retry(exc, retry_config.retry_exceptions) or attempt >= retry_config.max_attempts:
                        logger.exception(
                            "Async retry exhausted: function=%s attempt=%s/%s",
                            target.__name__,
                            attempt,
                            retry_config.max_attempts,
                        )
                        if recover_failed_tasks:
                            await _recover_failed_queue_jobs(recovery_queue_name)
                        raise RetryExhaustedError(f"{target.__name__} failed after {attempt} attempts") from exc

                    delay = _delay_for_attempt(retry_config, attempt)
                    logger.warning(
                        "Async retry scheduled: function=%s attempt=%s/%s delay=%.2fs error=%s",
                        target.__name__,
                        attempt,
                        retry_config.max_attempts,
                        delay,
                        exc,
                    )
                    await asyncio.sleep(delay)

            raise RetryExhaustedError(f"{target.__name__} failed after {retry_config.max_attempts} attempts") from last_error

        return wrapper

    return decorator(func) if func is not None else decorator


def retry_sync(
    func: Callable[..., T] | None = None,
    *,
    config: RetryConfig | None = None,
    max_attempts: int | None = None,
    base_delay_seconds: float | None = None,
    max_delay_seconds: float | None = None,
    timeout_seconds: float | None = None,
    jitter_seconds: float | None = None,
    retry_exceptions: tuple[type[BaseException], ...] | None = None,
) -> Callable[..., T]:
    """Synchronous retry decorator for SDKs that do not expose async clients."""
    overrides = {
        key: value
        for key, value in {
            "max_attempts": max_attempts,
            "base_delay_seconds": base_delay_seconds,
            "max_delay_seconds": max_delay_seconds,
            "timeout_seconds": timeout_seconds,
            "jitter_seconds": jitter_seconds,
            "retry_exceptions": retry_exceptions,
        }.items()
        if value is not None
    }
    retry_config = _normalize_config(config, **overrides)

    def decorator(target: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(target)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_error: BaseException | None = None
            for attempt in range(1, retry_config.max_attempts + 1):
                started_at = time.monotonic()
                try:
                    result = target(*args, **kwargs)
                    elapsed = time.monotonic() - started_at
                    if retry_config.timeout_seconds is not None and elapsed > retry_config.timeout_seconds:
                        raise TimeoutError(f"{target.__name__} exceeded {retry_config.timeout_seconds}s")
                    return result
                except BaseException as exc:
                    last_error = exc
                    if not _should_retry(exc, retry_config.retry_exceptions) or attempt >= retry_config.max_attempts:
                        logger.exception(
                            "Sync retry exhausted: function=%s attempt=%s/%s",
                            target.__name__,
                            attempt,
                            retry_config.max_attempts,
                        )
                        raise RetryExhaustedError(f"{target.__name__} failed after {attempt} attempts") from exc

                    delay = _delay_for_attempt(retry_config, attempt)
                    logger.warning(
                        "Sync retry scheduled: function=%s attempt=%s/%s delay=%.2fs error=%s",
                        target.__name__,
                        attempt,
                        retry_config.max_attempts,
                        delay,
                        exc,
                    )
                    time.sleep(delay)

            raise RetryExhaustedError(f"{target.__name__} failed after {retry_config.max_attempts} attempts") from last_error

        return wrapper

    return decorator(func) if func is not None else decorator


async def recover_failed_tasks(queue_name: str | None = None) -> dict[str, Any] | None:
    """Public recovery helper for failed Redis Queue jobs."""
    return await _recover_failed_queue_jobs(queue_name)
