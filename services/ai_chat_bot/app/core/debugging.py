import os
import time
from collections.abc import Callable
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import DEBUG_HTTP_BODY_LOGGING, DEBUG_HTTP_BODY_MAX_CHARS, DEBUG_HTTP_LOGGING
from app.core.logger import get_request_id, log_error, log_event

SENSITIVE_HEADERS = {"authorization", "cookie", "set-cookie", "x-hub-signature-256"}
SENSITIVE_ENV_KEYS = (
    "GROQ_API_KEY",
    "REDIS_URL",
    "MONGO_URI",
    "SMTP_EMAIL",
    "SMTP_PASSWORD",
    "EMAIL_USER",
    "EMAIL_PASS",
    "TWILIO_ACCOUNT_SID",
    "TWILIO_AUTH_TOKEN",
    "WHATSAPP_ACCESS_TOKEN",
    "WHATSAPP_PHONE_NUMBER_ID",
)


class DebugRequestMiddleware(BaseHTTPMiddleware):
    """Opt-in request/response diagnostics for local load testing and 500 analysis."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        started_at = time.perf_counter()
        request_body_preview = None
        if DEBUG_HTTP_BODY_LOGGING:
            body = await request.body()
            request_body_preview = _truncate(_decode_body(body))

            async def receive() -> dict[str, Any]:
                return {"type": "http.request", "body": body, "more_body": False}

            request = Request(request.scope, receive)

        if DEBUG_HTTP_LOGGING:
            log_event(
                "http_request_started",
                method=request.method,
                path=request.url.path,
                query=str(request.url.query),
                client=request.client.host if request.client else None,
                headers=_safe_headers(request.headers),
                body_preview=request_body_preview,
            )

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
            log_error(
                "http_request_exception",
                method=request.method,
                path=request.url.path,
                duration_ms=duration_ms,
                error_type=type(exc).__name__,
                diagnostics=diagnose_exception(exc),
                exc_info=True,
            )
            raise

        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        response_body_preview = None
        if DEBUG_HTTP_BODY_LOGGING:
            body_chunks = [chunk async for chunk in response.body_iterator]
            body = b"".join(body_chunks)
            response_body_preview = _truncate(_decode_body(body))
            response = Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
                background=response.background,
            )

        if DEBUG_HTTP_LOGGING or response.status_code >= 500:
            log_event(
                "http_request_finished",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                response_body_preview=response_body_preview,
            )

        response.headers["x-response-time-ms"] = str(duration_ms)
        return response


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        log_error(
            "request_validation_failed",
            method=request.method,
            path=request.url.path,
            errors=exc.errors(),
            request_id=get_request_id(),
        )
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": "validation_error",
                "detail": exc.errors(),
                "request_id": get_request_id(),
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        if exc.status_code >= 500:
            log_error(
                "http_exception",
                method=request.method,
                path=request.url.path,
                status_code=exc.status_code,
                detail=exc.detail,
                request_id=get_request_id(),
            )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": "http_error",
                "detail": exc.detail,
                "request_id": get_request_id(),
            },
            headers=exc.headers,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        log_error(
            "unhandled_exception",
            method=request.method,
            path=request.url.path,
            error_type=type(exc).__name__,
            diagnostics=diagnose_exception(exc),
            request_id=get_request_id(),
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "internal_server_error",
                "message": "Unexpected server error. Check application logs for diagnostics.",
                "diagnostics": diagnose_exception(exc),
                "request_id": get_request_id(),
            },
        )


def diagnose_exception(exc: Exception) -> dict[str, Any]:
    text = f"{type(exc).__name__}: {exc}".lower()
    hints: list[str] = []
    component = "application"

    if "redis" in text or "redist" in text or "redis_url" in text:
        component = "redis"
        hints.extend(
            [
                "Confirm REDIS_URL is set and reachable.",
                "Start Redis locally or set RATE_LIMIT_ENABLED=false for development-only load tests.",
            ]
        )
    if "mongo" in text or "pymongo" in text or "mongo_uri" in text:
        component = "mongodb"
        hints.extend(["Confirm MONGO_URI is set and reachable.", "Check MongoDB network/auth settings."])
    if "groq" in text or "api_key" in text or "environment" in text or "not configured" in text:
        component = "configuration"
        hints.extend(["Check missing environment variables.", "Use /test-email and startup logs for configuration validation."])
    if "validation" in text or "pydantic" in text:
        component = "payload"
        hints.append("Compare the request body/query parameters with the OpenAPI schema.")
    if "retrieval" in text or "embedding" in text or "faiss" in text:
        component = "retrieval"
        hints.extend(["Check vector index initialization.", "Validate embedding model availability and input size."])
    if "async" in text or "event loop" in text or "await" in text:
        component = "async"
        hints.append("Look for blocking calls or un-awaited coroutines in async request handlers.")

    return {
        "component": component,
        "hints": list(dict.fromkeys(hints)) or ["Inspect the traceback and request_id in server logs."],
        "missing_environment": _missing_environment_keys(),
    }


def _safe_headers(headers) -> dict[str, str]:
    return {key: ("<redacted>" if key.lower() in SENSITIVE_HEADERS else value) for key, value in headers.items()}


def _missing_environment_keys() -> list[str]:
    return [key for key in SENSITIVE_ENV_KEYS if not os.getenv(key)]


def _decode_body(body: bytes) -> str:
    try:
        return body.decode("utf-8", errors="replace")
    except Exception:
        return "<binary body>"


def _truncate(value: str | None) -> str | None:
    if value is None or len(value) <= DEBUG_HTTP_BODY_MAX_CHARS:
        return value
    return f"{value[:DEBUG_HTTP_BODY_MAX_CHARS]}...<truncated>"
