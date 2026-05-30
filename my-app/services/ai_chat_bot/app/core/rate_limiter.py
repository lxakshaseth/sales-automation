import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import redis.asyncio as redis
from redis.exceptions import RedisError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import (
    ENABLE_RATE_LIMIT,
    ENVIRONMENT,
    RATE_LIMIT_API_REQUESTS_PER_MINUTE,
    RATE_LIMIT_BYPASS_LOCALHOST,
    RATE_LIMIT_DISABLED_REASON,
    RATE_LIMIT_EMAILS_PER_MINUTE,
    RATE_LIMIT_ENABLED,
    RATE_LIMIT_MESSAGES_PER_MINUTE,
    RATE_LIMIT_WINDOW_SECONDS,
    REDIS_OPERATION_TIMEOUT_SECONDS,
    REDIS_URL,
)
from app.core.logger import log_error, log_event

RATE_LIMIT_PREFIX = "rate_limit"
DEFAULT_LIMIT_TYPE = "api"

_redis_client: redis.Redis | None = None


@dataclass(frozen=True)
class RateLimitRule:
    """Limit policy for one scope such as user, IP, or tool."""

    limit: int
    window_seconds: int = RATE_LIMIT_WINDOW_SECONDS


DEFAULT_LIMITS: dict[str, RateLimitRule] = {
    "message": RateLimitRule(limit=RATE_LIMIT_MESSAGES_PER_MINUTE),
    "email": RateLimitRule(limit=RATE_LIMIT_EMAILS_PER_MINUTE),
    "api": RateLimitRule(limit=RATE_LIMIT_API_REQUESTS_PER_MINUTE),
}

LOCALHOST_CLIENTS = {"127.0.0.1", "::1", "localhost", "testclient"}


class RateLimitError(RuntimeError):
    """Raised when Redis rate limiting fails unexpectedly."""


def log_rate_limiter_startup() -> None:
    """Emit one startup log that makes load-test limiter behavior unmistakable."""
    log_event(
        "rate_limiter_configuration",
        enabled=ENABLE_RATE_LIMIT,
        environment=ENVIRONMENT,
        api_limit_per_window=RATE_LIMIT_API_REQUESTS_PER_MINUTE,
        message_limit_per_window=RATE_LIMIT_MESSAGES_PER_MINUTE,
        email_limit_per_window=RATE_LIMIT_EMAILS_PER_MINUTE,
        window_seconds=RATE_LIMIT_WINDOW_SECONDS,
        localhost_bypass=RATE_LIMIT_BYPASS_LOCALHOST,
        disabled_reason=RATE_LIMIT_DISABLED_REASON or None,
    )


def _get_redis_client() -> redis.Redis:
    """Reuse one async Redis client for distributed rate limiting."""
    global _redis_client

    if _redis_client is None:
        if not REDIS_URL:
            raise RateLimitError("REDIS_URL is not configured")

        _redis_client = redis.from_url(
            REDIS_URL,
            decode_responses=True,
            health_check_interval=30,
            socket_connect_timeout=REDIS_OPERATION_TIMEOUT_SECONDS,
            socket_timeout=REDIS_OPERATION_TIMEOUT_SECONDS,
            retry_on_timeout=True,
        )

    return _redis_client


async def close_rate_limiter() -> None:
    """Close Redis resources during FastAPI shutdown or tests."""
    global _redis_client

    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None


def _current_window(now: int | None = None, window_seconds: int = RATE_LIMIT_WINDOW_SECONDS) -> int:
    return int((now or time.time()) // window_seconds)


def _rate_limit_key(scope: str, identifier: str, limit_type: str, window_seconds: int) -> str:
    window = _current_window(window_seconds=window_seconds)
    safe_identifier = str(identifier).replace(" ", "_")
    return f"{RATE_LIMIT_PREFIX}:{scope}:{limit_type}:{safe_identifier}:{window}"


def _resolve_rule(limit_type: str, limit: int | None = None, window_seconds: int | None = None) -> RateLimitRule:
    default = DEFAULT_LIMITS.get(limit_type, DEFAULT_LIMITS[DEFAULT_LIMIT_TYPE])
    return RateLimitRule(
        limit=limit if limit is not None else default.limit,
        window_seconds=window_seconds if window_seconds is not None else default.window_seconds,
    )


async def increment_usage(
    identifier: str,
    *,
    scope: str = "user",
    limit_type: str = DEFAULT_LIMIT_TYPE,
    window_seconds: int | None = None,
) -> dict[str, Any]:
    """Increment distributed usage counter and return current count."""
    rule = _resolve_rule(limit_type, window_seconds=window_seconds)
    key = _rate_limit_key(scope, identifier, limit_type, rule.window_seconds)

    try:
        client = _get_redis_client()
        pipe = client.pipeline()
        pipe.incr(key)
        pipe.expire(key, rule.window_seconds)
        count, _ = await asyncio.wait_for(pipe.execute(), timeout=REDIS_OPERATION_TIMEOUT_SECONDS)
        ttl = await asyncio.wait_for(client.ttl(key), timeout=REDIS_OPERATION_TIMEOUT_SECONDS)
    except (TimeoutError, RedisError) as exc:
        log_error("Rate limit increment failed", scope=scope, identifier=identifier, limit_type=limit_type, error_type=type(exc).__name__)
        raise RateLimitError("failed to increment rate limit usage") from exc

    return {
        "key": key,
        "scope": scope,
        "identifier": identifier,
        "limit_type": limit_type,
        "count": int(count),
        "ttl": max(0, int(ttl)),
        "window_seconds": rule.window_seconds,
    }


async def check_rate_limit(
    identifier: str,
    *,
    scope: str = "user",
    limit_type: str = DEFAULT_LIMIT_TYPE,
    limit: int | None = None,
    window_seconds: int | None = None,
    increment: bool = True,
) -> dict[str, Any]:
    """
    Check whether an identifier can perform an action.

    Set `increment=False` to only inspect current usage without consuming quota.
    """
    if not RATE_LIMIT_ENABLED:
        rule = _resolve_rule(limit_type, limit=limit, window_seconds=window_seconds)
        return {
            "allowed": True,
            "scope": scope,
            "identifier": str(identifier or "disabled"),
            "limit_type": limit_type,
            "limit": rule.limit,
            "count": 0,
            "remaining": rule.limit,
            "retry_after": 0,
            "reset_in": rule.window_seconds,
            "window_seconds": rule.window_seconds,
            "key": "rate_limit:disabled",
            "bypassed": True,
            "bypass_reason": RATE_LIMIT_DISABLED_REASON or "ENABLE_RATE_LIMIT=false",
        }

    if not identifier or not str(identifier).strip():
        raise ValueError("identifier is required")

    rule = _resolve_rule(limit_type, limit=limit, window_seconds=window_seconds)
    key = _rate_limit_key(scope, str(identifier).strip(), limit_type, rule.window_seconds)

    try:
        client = _get_redis_client()
        if increment:
            usage = await increment_usage(str(identifier).strip(), scope=scope, limit_type=limit_type, window_seconds=rule.window_seconds)
            count = usage["count"]
            ttl = usage["ttl"]
        else:
            raw_count = await asyncio.wait_for(client.get(key), timeout=REDIS_OPERATION_TIMEOUT_SECONDS)
            count = int(raw_count or 0)
            ttl = await asyncio.wait_for(client.ttl(key), timeout=REDIS_OPERATION_TIMEOUT_SECONDS)
            ttl = max(0, int(ttl))
    except (TimeoutError, RedisError) as exc:
        log_error("Rate limit check failed", scope=scope, identifier=identifier, limit_type=limit_type, error_type=type(exc).__name__)
        raise RateLimitError("failed to check rate limit") from exc

    allowed = count <= rule.limit
    remaining = max(0, rule.limit - count)
    result = {
        "allowed": allowed,
        "scope": scope,
        "identifier": str(identifier).strip(),
        "limit_type": limit_type,
        "limit": rule.limit,
        "count": count,
        "remaining": remaining,
        "retry_after": 0 if allowed else ttl,
        "reset_in": ttl,
        "window_seconds": rule.window_seconds,
        "key": key,
    }

    log_event("rate_limit_checked", **{key_: value for key_, value in result.items() if key_ != "key"})
    return result


async def reset_limit(
    identifier: str,
    *,
    scope: str = "user",
    limit_type: str = DEFAULT_LIMIT_TYPE,
    window_seconds: int | None = None,
) -> dict[str, Any]:
    """Clear the current rate-limit bucket for a user, IP, or tool."""
    rule = _resolve_rule(limit_type, window_seconds=window_seconds)
    key = _rate_limit_key(scope, identifier, limit_type, rule.window_seconds)

    try:
        deleted = await asyncio.wait_for(_get_redis_client().delete(key), timeout=REDIS_OPERATION_TIMEOUT_SECONDS)
    except (TimeoutError, RedisError) as exc:
        log_error("Rate limit reset failed", scope=scope, identifier=identifier, limit_type=limit_type, error_type=type(exc).__name__)
        raise RateLimitError("failed to reset rate limit") from exc

    return {"success": True, "key": key, "deleted": bool(deleted)}


async def check_tool_rate_limit(user_id: str, tool_name: str) -> dict[str, Any]:
    """Convenience helper for per-tool limits like 5 emails/minute."""
    limit_type = "email" if tool_name == "send_email" else "api"
    identifier = f"{user_id}:{tool_name}"
    return await check_rate_limit(identifier, scope="tool", limit_type=limit_type)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware enforcing distributed per-IP and optional per-user limits."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        if _should_bypass_request_rate_limit(request):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        user_id = request.headers.get("x-user-id")

        ip_result = await check_rate_limit(client_ip, scope="ip", limit_type="api")
        if not ip_result["allowed"]:
            return _rate_limited_response(ip_result)

        if user_id:
            user_result = await check_rate_limit(user_id, scope="user", limit_type="api")
            if not user_result["allowed"]:
                return _rate_limited_response(user_result)

        response = await call_next(request)
        response.headers["x-ratelimit-limit"] = str(ip_result["limit"])
        response.headers["x-ratelimit-remaining"] = str(ip_result["remaining"])
        response.headers["x-ratelimit-reset"] = str(ip_result["reset_in"])
        return response


def install_rate_limit_middleware(app) -> None:
    """Install rate limiting only when enabled, preserving a clean FastAPI middleware stack."""
    log_rate_limiter_startup()
    if RATE_LIMIT_ENABLED:
        app.add_middleware(RateLimitMiddleware)
        return

    # Do not add the middleware during Locust/testing runs. Direct helper calls
    # still use check_rate_limit(), which returns an allowed bypass result.
    log_event("rate_limiter_disabled", environment=ENVIRONMENT, reason=RATE_LIMIT_DISABLED_REASON)


def _should_bypass_request_rate_limit(request: Request) -> bool:
    if request.url.path in {"/docs", "/openapi.json", "/redoc"}:
        return True
    if not RATE_LIMIT_ENABLED:
        return True
    client_host = request.client.host if request.client else ""
    return bool(RATE_LIMIT_BYPASS_LOCALHOST and client_host in LOCALHOST_CLIENTS)


def _rate_limited_response(result: dict[str, Any]) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "error": "rate limit exceeded",
            "rate_limit": result,
        },
        headers={
            "retry-after": str(result["retry_after"]),
            "x-ratelimit-limit": str(result["limit"]),
            "x-ratelimit-remaining": str(result["remaining"]),
            "x-ratelimit-reset": str(result["reset_in"]),
        },
    )
