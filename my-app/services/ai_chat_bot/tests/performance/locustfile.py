import json
import logging
import os
import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

import gevent
from locust import between, events, task
from locust.contrib.fasthttp import FastHttpUser
from locust.exception import StopUser


logger = logging.getLogger("locust.ai_chat_bot")

DEFAULT_HOST = os.getenv("LOCUST_HOST", "http://127.0.0.1:8000")
MAX_REQUESTS_PER_USER = int(os.getenv("LOCUST_MAX_REQUESTS_PER_USER", "10"))
REQUEST_TIMEOUT_SECONDS = float(os.getenv("LOCUST_REQUEST_TIMEOUT_SECONDS", "16"))
SLOW_RESPONSE_MS = float(os.getenv("LOCUST_SLOW_RESPONSE_MS", "5000"))
MAX_DEBUG_BODY_CHARS = int(os.getenv("LOCUST_MAX_DEBUG_BODY_CHARS", "1000"))
RUN_TIME = os.getenv("LOCUST_RUN_TIME") or os.getenv("LOCUST_RUN_TIME_SECONDS")


@dataclass(frozen=True)
class ExpectedResponse:
    statuses: tuple[int, ...] = (200,)
    body_type: str = "json"
    validator: Callable[[Any], bool] | None = None
    description: str = ""


def env_enabled(name: str, *, default: bool = False) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def parse_duration_seconds(value: str | None) -> int | None:
    if not value:
        return None
    text = value.strip().lower()
    multiplier = 1
    if text.endswith("ms"):
        return max(1, int(float(text[:-2]) / 1000))
    if text.endswith("s"):
        text = text[:-1]
    elif text.endswith("m"):
        text = text[:-1]
        multiplier = 60
    elif text.endswith("h"):
        text = text[:-1]
        multiplier = 3600
    return int(float(text) * multiplier)


@events.init.add_listener
def configure_run_time(environment, **_: Any) -> None:
    seconds = parse_duration_seconds(RUN_TIME)
    if not seconds:
        return

    def stop_runner() -> None:
        if environment.runner:
            logger.info("event=locust_auto_stop run_time_seconds=%s", seconds)
            environment.runner.quit()

    gevent.spawn_later(seconds, stop_runner)


def truncate(value: Any) -> str:
    text = value if isinstance(value, str) else repr(value)
    if len(text) <= MAX_DEBUG_BODY_CHARS:
        return text
    return f"{text[:MAX_DEBUG_BODY_CHARS]}...<truncated>"


def request_payload_size(*, json_payload: Any | None = None, data_payload: Any | None = None) -> int:
    if json_payload is not None:
        return len(json.dumps(json_payload, default=str).encode("utf-8"))
    if data_payload is not None:
        return len(str(data_payload).encode("utf-8"))
    return 0


def parse_response_body(response, body_type: str) -> tuple[Any, str | None]:
    text = response.text or ""
    if not text.strip():
        return text, "empty response body"
    if body_type == "json":
        try:
            return response.json(), None
        except Exception as exc:
            return text, f"malformed JSON: {type(exc).__name__}"
    return text, None


def root_ok(body: Any) -> bool:
    return isinstance(body, dict) and body.get("status") == "running"


def reports_ok(body: Any) -> bool:
    return isinstance(body, dict) and isinstance(body.get("reports"), list)


def emails_ok(body: Any) -> bool:
    return isinstance(body, dict) and isinstance(body.get("emails"), list)


def ask_ok(body: Any) -> bool:
    return isinstance(body, dict) and isinstance(body.get("response"), str) and bool(body["response"].strip())


def owner_email_ok(body: Any) -> bool:
    return isinstance(body, dict) and isinstance(body.get("email"), str) and "active" in body


def delete_ok(body: Any) -> bool:
    return isinstance(body, dict) and isinstance(body.get("removed"), bool)


def twiml_ok(body: Any) -> bool:
    return isinstance(body, str) and "<Response>" in body and "<Message>" in body


class BaseAPIUser(FastHttpUser):
    abstract = True
    host = DEFAULT_HOST
    wait_time = between(1, 3)

    def on_start(self) -> None:
        self.user_id = f"locust-{uuid4().hex[:12]}"
        self.request_count = 0
        self.created_emails: set[str] = set()

    def on_stop(self) -> None:
        self.cleanup_created_emails()

    def get_headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        """Return a concrete dict. FastHttpUser cannot accept a method object here."""
        headers = {
            "User-Agent": "locust-load-test",
            "Content-Type": "application/json",
            "x-user-id": self.user_id,
            "x-load-test": "locust",
        }
        if env_enabled("LOAD_TEST_MODE"):
            headers["x-load-test-mode"] = "true"
        if env_enabled("DISABLE_RATE_LIMIT"):
            headers["x-disable-rate-limit"] = "true"
        if env_enabled("MOCK_AI"):
            headers["x-mock-ai"] = "true"
        if extra:
            headers.update(extra)
        if not isinstance(headers, dict):
            raise TypeError("headers must be a dictionary")
        return headers

    def ensure_request_budget(self) -> None:
        if self.request_count >= MAX_REQUESTS_PER_USER:
            raise StopUser()
        self.request_count += 1

    def request_json(
        self,
        method: str,
        path: str,
        *,
        name: str,
        expected: ExpectedResponse,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
        timeout: float | None = None,
        count_toward_limit: bool = True,
    ) -> Any:
        return self._request(
            method,
            path,
            name=name,
            expected=expected,
            params=params,
            json_payload=payload,
            headers=self.get_headers(),
            timeout=timeout,
            count_toward_limit=count_toward_limit,
        )

    def request_form(
        self,
        method: str,
        path: str,
        *,
        name: str,
        expected: ExpectedResponse,
        payload: dict[str, Any],
        timeout: float | None = None,
    ) -> Any:
        return self._request(
            method,
            path,
            name=name,
            expected=expected,
            data_payload=payload,
            headers=self.get_headers({"Content-Type": "application/x-www-form-urlencoded"}),
            timeout=timeout,
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        name: str,
        expected: ExpectedResponse,
        headers: dict[str, str],
        params: dict[str, Any] | None = None,
        json_payload: dict[str, Any] | None = None,
        data_payload: dict[str, Any] | None = None,
        timeout: float | None = None,
        count_toward_limit: bool = True,
    ) -> Any:
        if count_toward_limit:
            self.ensure_request_budget()
        if not isinstance(headers, dict):
            raise TypeError(f"headers for {name} must be dict, got {type(headers).__name__}")

        request_size = request_payload_size(json_payload=json_payload, data_payload=data_payload)
        started_at = time.perf_counter()
        try:
            with self.client.request(
                method,
                path,
                name=name,
                params=params,
                json=json_payload,
                data=data_payload,
                headers=headers,
                catch_response=True,
                timeout=timeout or REQUEST_TIMEOUT_SECONDS,
            ) as response:
                latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
                response_size = len(response.content or b"")
                body, parse_error = parse_response_body(response, expected.body_type)
                url = f"{self.host}{path}"

                logger.info(
                    "event=request url=%s name=%s method=%s status=%s latency_ms=%s request_bytes=%s response_bytes=%s",
                    url,
                    name,
                    method,
                    response.status_code,
                    latency_ms,
                    request_size,
                    response_size,
                )

                failures: list[str] = []
                if response.status_code not in expected.statuses:
                    failures.append(f"unexpected status {response.status_code}; expected {expected.statuses}")
                if latency_ms > SLOW_RESPONSE_MS:
                    failures.append(f"slow response {latency_ms}ms > {SLOW_RESPONSE_MS}ms")
                    logger.warning("event=slow_response url=%s name=%s latency_ms=%s", url, name, latency_ms)
                if parse_error:
                    failures.append(parse_error)
                if expected.validator and not expected.validator(body):
                    failures.append(f"validation failed: {expected.description or name}")

                if failures:
                    logger.error(
                        "event=request_failure url=%s status=%s latency_ms=%s payload=%s body=%s failures=%s",
                        url,
                        response.status_code,
                        latency_ms,
                        truncate(json_payload if json_payload is not None else data_payload),
                        truncate(body),
                        failures,
                    )
                    response.failure("; ".join(failures))
                    return body

                response.success()
                return body
        except StopUser:
            raise
        except Exception as exc:
            latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
            logger.exception("event=request_exception name=%s path=%s latency_ms=%s error=%s", name, path, latency_ms, exc)
            events.request.fire(
                request_type=method,
                name=name,
                response_time=latency_ms,
                response_length=0,
                exception=exc,
                context={},
            )
            return None

    def owner_email_payload(self) -> dict[str, Any]:
        email = f"loadtest-{self.user_id}-{uuid4().hex[:8]}@example.com"
        self.created_emails.add(email)
        return {"email": email, "active": True}

    def cleanup_created_emails(self) -> None:
        for email in list(getattr(self, "created_emails", set())):
            try:
                self.request_json(
                    "DELETE",
                    "/owner-settings/emails",
                    name="cleanup:DELETE /owner-settings/emails",
                    params={"email": email},
                    expected=ExpectedResponse(validator=delete_ok),
                    count_toward_limit=False,
                )
            finally:
                self.created_emails.discard(email)

    @staticmethod
    def twilio_form_payload(user_id: str) -> dict[str, str]:
        phone_digits = "".join(ch for ch in user_id if ch.isdigit())[-10:] or str(random.randint(7000000000, 9999999999))
        return {
            "MessageSid": f"SM{uuid4().hex[:32]}",
            "SmsMessageSid": f"SM{uuid4().hex[:32]}",
            "AccountSid": f"AC{uuid4().hex[:32]}",
            "MessagingServiceSid": f"MG{uuid4().hex[:32]}",
            "From": f"whatsapp:+91{phone_digits}",
            "To": "whatsapp:+14155238886",
            "Body": random.choice(
                [
                    "Need WhatsApp automation pricing.",
                    "I want an AI chatbot demo.",
                    "Can you qualify leads from WhatsApp?",
                    "Please share CRM integration details.",
                ]
            ),
            "NumMedia": "0",
        }


class SmokeTestUser(BaseAPIUser):
    """Lightweight read-only profile for route health and latency baselines."""

    weight = 5

    @task(4)
    def root(self) -> None:
        self.request_json("GET", "/", name="smoke:GET /", expected=ExpectedResponse(validator=root_ok))

    @task(3)
    def report_history(self) -> None:
        self.request_json(
            "GET",
            "/reports/history",
            name="smoke:GET /reports/history",
            params={"limit": 10},
            expected=ExpectedResponse(validator=reports_ok),
        )

    @task(3)
    def owner_settings_emails(self) -> None:
        self.request_json(
            "GET",
            "/owner-settings/emails",
            name="smoke:GET /owner-settings/emails",
            params={"active_only": False},
            expected=ExpectedResponse(validator=emails_ok),
        )


class HeavyAIUser(BaseAPIUser):
    """Low-weight AI webhook profile. Use MOCK_AI=true for backend-only load tests."""

    weight = 1

    @task(1)
    def twilio_whatsapp_webhook(self) -> None:
        self.request_form(
            "POST",
            "/webhook/twilio/whatsapp",
            name="ai:POST /webhook/twilio/whatsapp",
            payload=self.twilio_form_payload(self.user_id),
            timeout=REQUEST_TIMEOUT_SECONDS,
            expected=ExpectedResponse(body_type="text", validator=twiml_ok, description="Twilio XML response"),
        )

    @task(1)
    def legacy_twilio_webhook(self) -> None:
        self.request_form(
            "POST",
            "/webhook",
            name="ai:POST /webhook",
            payload=self.twilio_form_payload(self.user_id),
            timeout=REQUEST_TIMEOUT_SECONDS,
            expected=ExpectedResponse(body_type="text", validator=twiml_ok, description="legacy Twilio XML response"),
        )


class StressTestUser(BaseAPIUser):
    """Mixed API stress profile with cleanup to avoid test-data growth."""

    weight = 2

    @task(2)
    def ask(self) -> None:
        self.request_json(
            "GET",
            "/ask",
            name="stress:GET /ask",
            params={"q": random.choice(["Share pricing", "How does WhatsApp automation work?", "Book a demo"])},
            expected=ExpectedResponse(validator=ask_ok),
        )

    @task(3)
    def owner_email_lifecycle(self) -> None:
        payload = self.owner_email_payload()
        created = self.request_json(
            "POST",
            "/owner-settings/emails",
            name="stress:POST /owner-settings/emails",
            payload=payload,
            expected=ExpectedResponse(validator=owner_email_ok),
        )
        if not owner_email_ok(created):
            return

        self.request_json(
            "PATCH",
            "/owner-settings/emails",
            name="stress:PATCH /owner-settings/emails",
            payload={**payload, "active": random.choice([True, False])},
            expected=ExpectedResponse(validator=owner_email_ok),
        )
        self.request_json(
            "DELETE",
            "/owner-settings/emails",
            name="stress:DELETE /owner-settings/emails",
            params={"email": payload["email"]},
            expected=ExpectedResponse(validator=delete_ok),
        )
        self.created_emails.discard(payload["email"])
