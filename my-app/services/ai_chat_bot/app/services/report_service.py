import asyncio
import html
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import redis.asyncio as redis
from redis.exceptions import RedisError

from app.config.settings import settings
from app.core.config import REDIS_URL
from app.core.logger import log_error, log_event, log_info
from app.core.performance import measure
from app.models.report_models import ConversationReport
from app.models.summary_models import EmailReport
from app.services.ai_summary_service import generate_ai_sales_summary
from app.services.conversation_service import get_conversation_history, get_conversation_state
from app.services.email_service import EmailServiceError, send_html_email
from app.services.owner_settings_service import get_active_owner_emails
from app.services.transcript_service import normalize_transcript
from app.utils.ttl_cache import TTLCache

REPORT_KEY_PREFIX = "agent:report"
REPORT_HISTORY_KEY = "agent:report:history"
REPORT_TTL_SECONDS = int(os.getenv("REPORT_TTL_SECONDS", str(90 * 24 * 60 * 60)))
TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates"

_redis_client: redis.Redis | None = None
_memory_reports: dict[str, ConversationReport] = {}
_memory_history: list[str] = []
_history_cache: TTLCache[list[ConversationReport]] = TTLCache(ttl_seconds=settings.report_history_cache_ttl_seconds)


class ReportServiceError(RuntimeError):
    """Raised when report generation or storage fails."""


def _get_redis_client() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        if not REDIS_URL:
            raise ReportServiceError("REDIS_URL is not configured")
        _redis_client = redis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=settings.redis_operation_timeout_seconds,
            socket_timeout=settings.redis_operation_timeout_seconds,
            retry_on_timeout=True,
            health_check_interval=30,
        )
    return _redis_client


async def _redis_call(operation: str, coro):
    async with measure("redis", f"reports.{operation}"):
        return await asyncio.wait_for(coro, timeout=settings.redis_operation_timeout_seconds)


async def close_report_service_client() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None


def _escape(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def _list_items(values: list[str]) -> str:
    safe_values = values or ["Not captured"]
    return "".join(f"<li>{_escape(value)}</li>" for value in safe_values)


def _render_template(template_name: str, context: dict[str, Any]) -> str:
    template = (TEMPLATE_DIR / template_name).read_text(encoding="utf-8")
    for key, value in context.items():
        template = template.replace("{{" + key + "}}", str(value))
    return template


def build_report_subject(report: ConversationReport) -> str:
    lead_type = str(report.lead_analysis.get("lead_type") or "LEAD").upper()
    return f"[{lead_type}] Conversation Summary - {report.client_name} - {report.company_name}"


def render_report_html(report: ConversationReport) -> str:
    lead = report.lead_analysis or {}
    date_text = report.date_time.strftime("%Y-%m-%d %I:%M %p")
    log_info("Preparing HTML email...", report_id=report.report_id, user_id=report.user_id)
    try:
        html_body = _render_template(
            "sales_summary_template.html",
            {
                "company_name": _escape(report.company_name),
                "client_name": _escape(report.client_name),
                "client_phone_number": _escape(report.client_phone_number),
                "client_email": _escape(report.client_email or "Not captured"),
                "conversation_source": _escape(report.conversation_source),
                "date_time": _escape(date_text),
                "language": _escape(report.language),
                "topic_items": _list_items(report.topic_of_discussion),
                "requirement_items": _list_items(report.client_requirements),
                "lead_type": _escape(lead.get("lead_type") or "Needs Review"),
                "interest_level": _escape(lead.get("interest_level") or "Unknown"),
                "buying_intent": _escape(lead.get("buying_intent") or "Unknown"),
                "closing_probability": _escape(lead.get("estimated_closing_probability") or 0),
                "ai_remarks": _escape(report.ai_remarks),
                "next_action_items": _list_items(report.next_actions),
                "full_conversation_summary": _escape(report.full_conversation_summary),
                "transcript_html": report.transcript.html if report.transcript else "",
            },
        )
    except Exception as exc:
        log_error("HTML report rendering failed", report_id=report.report_id, error_type=type(exc).__name__)
        raise ReportServiceError("failed to render sales report HTML") from exc
    log_event("html_report_rendered", report_id=report.report_id, user_id=report.user_id)
    return html_body


def render_report_text(report: ConversationReport) -> str:
    lead = report.lead_analysis or {}
    lines = [
        "SALES CONVERSATION REPORT",
        "",
        f"Company Name: {report.company_name}",
        f"Client Name: {report.client_name}",
        f"Client Phone Number: {report.client_phone_number}",
        f"Client Email: {report.client_email or 'Not captured'}",
        f"Conversation Source: {report.conversation_source}",
        f"Date & Time: {report.date_time.strftime('%Y-%m-%d %I:%M %p')}",
        f"Language: {report.language}",
        "",
        "TOPIC OF DISCUSSION",
        *[f"- {item}" for item in report.topic_of_discussion],
        "",
        "CLIENT REQUIREMENTS",
        *[f"- {item}" for item in report.client_requirements],
        "",
        "LEAD ANALYSIS",
        f"Lead Type: {lead.get('lead_type', 'Needs Review')}",
        f"Interest Level: {lead.get('interest_level', 'Unknown')}",
        f"Buying Intent: {lead.get('buying_intent', 'Unknown')}",
        f"Estimated Closing Probability: {lead.get('estimated_closing_probability', 0)}%",
        "",
        "AI REMARKS",
        report.ai_remarks,
        "",
        "NEXT ACTIONS",
        *[f"- {item}" for item in report.next_actions],
        "",
        "FULL CONVERSATION SUMMARY",
        report.full_conversation_summary,
    ]
    return "\n".join(lines)


async def save_report(report: ConversationReport) -> ConversationReport:
    """Store reports for CRM sync and history lookups. TODO: replace with CRM DB table."""
    _memory_reports[report.report_id] = report
    if report.report_id not in _memory_history:
        _memory_history.insert(0, report.report_id)
    _history_cache.invalidate_prefix("history:")
    try:
        client = _get_redis_client()
        async with measure("redis", "reports.save", report_id=report.report_id):
            pipe = client.pipeline()
            pipe.set(f"{REPORT_KEY_PREFIX}:{report.report_id}", report.model_dump_json(), ex=REPORT_TTL_SECONDS)
            pipe.lrem(REPORT_HISTORY_KEY, 0, report.report_id)
            pipe.lpush(REPORT_HISTORY_KEY, report.report_id)
            pipe.ltrim(REPORT_HISTORY_KEY, 0, 499)
            await asyncio.wait_for(pipe.execute(), timeout=settings.redis_operation_timeout_seconds)
    except (TimeoutError, ReportServiceError, RedisError) as exc:
        log_error("Report Redis persistence failed", report_id=report.report_id, error_type=type(exc).__name__)
    return report


async def get_report(report_id: str) -> ConversationReport | None:
    if report_id in _memory_reports:
        return _memory_reports[report_id]
    try:
        raw_value = await _redis_call("get", _get_redis_client().get(f"{REPORT_KEY_PREFIX}:{report_id}"))
    except (TimeoutError, ReportServiceError, RedisError):
        return None
    if not raw_value:
        return None
    return ConversationReport.model_validate_json(raw_value)


async def list_reports(limit: int = 50) -> list[ConversationReport]:
    limit = max(1, min(limit, 200))
    cache_key = f"history:{limit}"
    cached = _history_cache.get(cache_key)
    if cached is not None:
        return cached

    ids = _memory_history[:limit]
    try:
        redis_ids = await _redis_call("history_ids", _get_redis_client().lrange(REPORT_HISTORY_KEY, 0, max(0, limit - 1)))
        ids = list(dict.fromkeys([*redis_ids, *ids]))[:limit]
    except (TimeoutError, ReportServiceError, RedisError):
        pass

    reports: list[ConversationReport] = []
    missing_ids = [report_id for report_id in ids if report_id not in _memory_reports]
    reports.extend(_memory_reports[report_id] for report_id in ids if report_id in _memory_reports)

    if missing_ids:
        try:
            keys = [f"{REPORT_KEY_PREFIX}:{report_id}" for report_id in missing_ids]
            raw_values = await _redis_call("history_mget", _get_redis_client().mget(keys))
            for raw_value in raw_values:
                if raw_value:
                    report = ConversationReport.model_validate_json(raw_value)
                    _memory_reports[report.report_id] = report
                    reports.append(report)
        except (TimeoutError, ReportServiceError, RedisError, ValueError) as exc:
            log_error("Report history Redis read failed", error_type=type(exc).__name__)

    order = {report_id: index for index, report_id in enumerate(ids)}
    reports = sorted(reports, key=lambda item: order.get(item.report_id, len(order)))[:limit]
    _history_cache.set(cache_key, reports, ttl_seconds=settings.report_history_cache_ttl_seconds)
    return reports


async def send_report_email(report: ConversationReport, recipients: list[str] | None = None, *, raise_on_failure: bool = False) -> EmailReport:
    resolved_recipients = recipients or await get_active_owner_emails()
    log_info("Rendering sales report email...", report_id=report.report_id, recipients=resolved_recipients)
    html_body = render_report_html(report)
    text_body = render_report_text(report)
    email_report = EmailReport(
        subject=build_report_subject(report),
        recipients=resolved_recipients,
        html_body=html_body,
        text_body=text_body,
    )
    if not resolved_recipients:
        email_report.error = "no active owner emails configured"
        log_error("Sales report email skipped", report_id=report.report_id, error=email_report.error)
        if raise_on_failure:
            raise EmailServiceError(email_report.error)
        return email_report
    try:
        await send_html_email(resolved_recipients, email_report.subject, text_body, html_body)
        email_report.sent = True
        email_report.sent_at = datetime.now(UTC)
        log_event("sales_report_email_sent", report_id=report.report_id, recipients=resolved_recipients)
    except EmailServiceError as exc:
        email_report.error = str(exc)
        log_error("Sales report email failed", report_id=report.report_id, error=str(exc))
        if raise_on_failure:
            report.email = email_report
            await save_report(report)
            raise
    report.email = email_report
    await save_report(report)
    return email_report


async def generate_conversation_report(
    *,
    user_id: str,
    company_name: str = "INDUX TECHNOLOGY",
    conversation_source: str = "WhatsApp",
    metadata: dict[str, Any] | None = None,
) -> ConversationReport:
    log_info("Generating AI summary...", user_id=user_id, source=conversation_source)
    state = await get_conversation_state(user_id)
    history = await get_conversation_history(user_id)
    transcript = normalize_transcript(user_id, history)
    phone_number = str((state or {}).get("phone_number") or user_id)
    ai_summary = await generate_ai_sales_summary(
        user_id=user_id,
        transcript=transcript,
        company_name=company_name,
        conversation_source=conversation_source,
        phone_number=phone_number,
        metadata=metadata or {},
    )
    report = ConversationReport.from_ai_summary(
        report_id=f"rep_{uuid4().hex}",
        user_id=user_id,
        ai_summary=ai_summary,
        transcript=transcript,
        metadata=metadata or {},
    )
    await save_report(report)
    log_event("sales_report_generated", report_id=report.report_id, user_id=user_id, lead_type=report.lead_analysis.get("lead_type"))
    return report


async def generate_and_send_report(
    *,
    user_id: str,
    company_name: str = "INDUX TECHNOLOGY",
    conversation_source: str = "WhatsApp",
    recipients: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    raise_on_email_failure: bool = False,
) -> ConversationReport:
    log_event("sales_report_generation_started", user_id=user_id, source=conversation_source)
    report = await generate_conversation_report(
        user_id=user_id,
        company_name=company_name,
        conversation_source=conversation_source,
        metadata=metadata,
    )
    await send_report_email(report, recipients=recipients, raise_on_failure=raise_on_email_failure)
    if report.email and report.email.sent:
        log_info("Summary email sent successfully", report_id=report.report_id, user_id=user_id)
    return report
