from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TranscriptMessage(BaseModel):
    role: Literal["user", "assistant", "system", "unknown"] = "unknown"
    content: str = Field(default="", max_length=8000)
    timestamp: str | None = None

    @field_validator("content")
    @classmethod
    def clean_content(cls, value: str) -> str:
        return str(value or "").strip()


class LeadAnalysis(BaseModel):
    lead_type: str = Field(default="Needs Review", max_length=80)
    interest_level: str = Field(default="Unknown", max_length=80)
    buying_intent: str = Field(default="Unknown", max_length=80)
    estimated_closing_probability: int = Field(default=0, ge=0, le=100)


class AISummary(BaseModel):
    company_name: str = Field(default="INDUX TECHNOLOGY", max_length=160)
    client_name: str = Field(default="Unknown", max_length=160)
    client_phone_number: str = Field(default="", max_length=40)
    client_email: str = Field(default="", max_length=254)
    conversation_source: str = Field(default="WhatsApp", max_length=80)
    language: str = Field(default="Unknown", max_length=80)
    topic_of_discussion: list[str] = Field(default_factory=list)
    client_requirements: list[str] = Field(default_factory=list)
    lead_analysis: LeadAnalysis = Field(default_factory=LeadAnalysis)
    ai_remarks: str = Field(default="", max_length=4000)
    next_actions: list[str] = Field(default_factory=list)
    full_conversation_summary: str = Field(default="", max_length=8000)
    raw_ai_payload: dict[str, Any] = Field(default_factory=dict)


class TranscriptReport(BaseModel):
    user_id: str
    messages: list[TranscriptMessage] = Field(default_factory=list)
    plain_text: str = ""
    html: str = ""


class EmailReport(BaseModel):
    subject: str
    recipients: list[str] = Field(default_factory=list)
    html_body: str
    text_body: str
    sent: bool = False
    error: str | None = None
    sent_at: datetime | None = None
