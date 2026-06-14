from fastapi import APIRouter, HTTPException, Query

from app.core.logger import log_error, log_event
from app.models.report_models import (
    ConversationReport,
    ReportGenerateRequest,
    ReportGenerateResponse,
    ReportHistoryResponse,
    SendReportEmailRequest,
)
from app.services.report_service import generate_and_send_report, generate_conversation_report, get_report, list_reports, send_report_email

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/generate", response_model=ReportGenerateResponse)
async def generate_report(request: ReportGenerateRequest) -> ReportGenerateResponse:
    """
    Generate an AI sales conversation report.

    Set async_processing=true to enqueue Celery. Otherwise the report is generated
    in the request lifecycle, which is convenient for local testing.
    """
    if request.async_processing:
        try:
            from app.tasks.summary_tasks import generate_and_email_report_task, generate_summary_task

            task = (
                generate_and_email_report_task.delay(
                    request.user_id,
                    request.company_name,
                    request.conversation_source,
                    request.recipients,
                    request.metadata,
                )
                if request.send_email
                else generate_summary_task.delay(
                    request.user_id,
                    request.company_name,
                    request.conversation_source,
                    request.metadata,
                )
            )
            log_event("sales_report_task_queued", user_id=request.user_id, task_id=task.id)
            return ReportGenerateResponse(queued=True, task_id=task.id)
        except Exception as exc:
            log_error("Sales report task queue failed", user_id=request.user_id, error_type=type(exc).__name__)
            raise HTTPException(status_code=503, detail="failed to queue report task") from exc

    report = (
        await generate_and_send_report(
            user_id=request.user_id,
            company_name=request.company_name,
            conversation_source=request.conversation_source,
            recipients=request.recipients,
            metadata=request.metadata,
        )
        if request.send_email
        else await generate_conversation_report(
            user_id=request.user_id,
            company_name=request.company_name,
            conversation_source=request.conversation_source,
            metadata=request.metadata,
        )
    )
    return ReportGenerateResponse(queued=False, report=report)


@router.post("/send-email")
async def email_report(request: SendReportEmailRequest) -> dict:
    report = await get_report(request.report_id)
    if not report:
        raise HTTPException(status_code=404, detail="report not found")
    email = await send_report_email(report, recipients=request.recipients)
    return email.model_dump(mode="json")


@router.get("/history", response_model=ReportHistoryResponse)
async def report_history(limit: int = Query(50, ge=1, le=200)) -> ReportHistoryResponse:
    return ReportHistoryResponse(reports=await list_reports(limit=limit))


@router.get("/{report_id}", response_model=ConversationReport)
async def read_report(report_id: str) -> ConversationReport:
    report = await get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="report not found")
    return report
