from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.summary_models import AISummary, EmailReport, TranscriptMessage, TranscriptReport, utc_now


class ReportGenerateRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=160)
    company_name: str = Field(default="INDUX TECHNOLOGY", max_length=160)
    conversation_source: str = Field(default="WhatsApp", max_length=80)
    send_email: bool = True
    async_processing: bool = False
    recipients: list[str] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SendReportEmailRequest(BaseModel):
    report_id: str = Field(..., min_length=1, max_length=120)
    recipients: list[str] | None = None


class ConversationReport(BaseModel):
    report_id: str
    user_id: str
    company_name: str = "INDUX TECHNOLOGY"
    client_name: str = "Unknown"
    client_phone_number: str = ""
    client_email: str = ""
    conversation_source: str = "WhatsApp"
    date_time: datetime = Field(default_factory=utc_now)
    language: str = "Unknown"
    topic_of_discussion: list[str] = Field(default_factory=list)
    client_requirements: list[str] = Field(default_factory=list)
    lead_analysis: dict[str, Any] = Field(default_factory=dict)
    ai_remarks: str = ""
    next_actions: list[str] = Field(default_factory=list)
    full_conversation_summary: str = ""
    transcript: TranscriptReport | None = None
    email: EmailReport | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)

    @classmethod
    def from_ai_summary(
        cls,
        *,
        report_id: str,
        user_id: str,
        ai_summary: AISummary,
        transcript: TranscriptReport,
        metadata: dict[str, Any] | None = None,
    ) -> "ConversationReport":
        return cls(
            report_id=report_id,
            user_id=user_id,
            company_name=ai_summary.company_name,
            client_name=ai_summary.client_name,
            client_phone_number=ai_summary.client_phone_number,
            client_email=ai_summary.client_email,
            conversation_source=ai_summary.conversation_source,
            language=ai_summary.language,
            topic_of_discussion=ai_summary.topic_of_discussion,
            client_requirements=ai_summary.client_requirements,
            lead_analysis=ai_summary.lead_analysis.model_dump(),
            ai_remarks=ai_summary.ai_remarks,
            next_actions=ai_summary.next_actions,
            full_conversation_summary=ai_summary.full_conversation_summary,
            transcript=transcript,
            metadata=metadata or {},
        )


class ReportGenerateResponse(BaseModel):
    queued: bool = False
    task_id: str | None = None
    report: ConversationReport | None = None


class ReportHistoryResponse(BaseModel):
    reports: list[ConversationReport]
