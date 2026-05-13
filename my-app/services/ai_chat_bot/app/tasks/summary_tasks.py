import asyncio
from typing import Any

from celery.utils.log import get_task_logger

from app.services.report_service import generate_and_send_report, generate_conversation_report, get_report, send_report_email
from app.workers.celery_app import celery_app

logger = get_task_logger(__name__)


@celery_app.task(bind=True, name="reports.generate_summary", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def generate_summary_task(
    self,
    user_id: str,
    company_name: str = "INDUX TECHNOLOGY",
    conversation_source: str = "WhatsApp",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate and persist an AI conversation report in a Celery worker."""
    logger.info("Celery summary task started: task_id=%s user_id=%s", self.request.id, user_id)
    report = asyncio.run(
        generate_conversation_report(
            user_id=user_id,
            company_name=company_name,
            conversation_source=conversation_source,
            metadata=metadata or {},
        )
    )
    logger.info("Celery summary task completed: task_id=%s report_id=%s", self.request.id, report.report_id)
    return report.model_dump(mode="json")


@celery_app.task(bind=True, name="reports.generate_and_email", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def generate_and_email_report_task(
    self,
    user_id: str,
    company_name: str = "INDUX TECHNOLOGY",
    conversation_source: str = "WhatsApp",
    recipients: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate a report and email it to the configured sales/admin team."""
    logger.info("Celery report email task started: task_id=%s user_id=%s", self.request.id, user_id)
    report = asyncio.run(
        generate_and_send_report(
            user_id=user_id,
            company_name=company_name,
            conversation_source=conversation_source,
            recipients=recipients,
            metadata=metadata or {},
            raise_on_email_failure=True,
        )
    )
    sent = bool(report.email and report.email.sent)
    logger.info("Celery report email task completed: task_id=%s report_id=%s sent=%s", self.request.id, report.report_id, sent)
    return report.model_dump(mode="json")


@celery_app.task(bind=True, name="reports.send_email", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def send_report_email_task(self, report_id: str, recipients: list[str] | None = None) -> dict[str, Any]:
    """Send an existing report email from a Celery worker."""

    async def _send() -> dict[str, Any]:
        logger.info("Celery send existing report email started: task_id=%s report_id=%s", self.request.id, report_id)
        report = await get_report(report_id)
        if not report:
            logger.error("Report not found for email task: task_id=%s report_id=%s", self.request.id, report_id)
            return {"sent": False, "error": "report_not_found", "report_id": report_id}
        email = await send_report_email(report, recipients=recipients)
        logger.info("Celery send existing report email completed: task_id=%s report_id=%s sent=%s", self.request.id, report_id, email.sent)
        return email.model_dump(mode="json")

    return asyncio.run(_send())


@celery_app.task(bind=True, name="reports.format_transcript", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def format_transcript_task(self, user_id: str) -> dict[str, Any]:
    """Generate a report transcript section for worker-level verification."""

    async def _format() -> dict[str, Any]:
        logger.info("Celery transcript task started: task_id=%s user_id=%s", self.request.id, user_id)
        report = await generate_conversation_report(user_id=user_id, metadata={"task": "format_transcript"})
        return report.transcript.model_dump(mode="json") if report.transcript else {}

    return asyncio.run(_format())


@celery_app.task(bind=True, name="reports.analyze_lead", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def analyze_lead_task(self, user_id: str) -> dict[str, Any]:
    """Run lead analysis by generating the report and returning only lead fields."""
    logger.info("Celery lead analysis task started: task_id=%s user_id=%s", self.request.id, user_id)
    report = asyncio.run(generate_conversation_report(user_id=user_id, metadata={"task": "analyze_lead"}))
    logger.info("Celery lead analysis task completed: task_id=%s report_id=%s", self.request.id, report.report_id)
    return report.lead_analysis
