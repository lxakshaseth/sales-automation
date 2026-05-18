from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from app.models.compression_models import TokenUsage


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


class SummarizationConfig(BaseModel):
    model_name: str = "llama-3.3-70b-versatile"
    max_input_tokens: int = Field(default=6000, ge=500)
    max_summary_tokens: int = Field(default=900, ge=100)
    preserve_recent_messages: int = Field(default=6, ge=0, le=50)
    min_messages_to_summarize: int = Field(default=20, ge=2)
    target_compression_ratio: float = Field(default=0.25, ge=0.05, le=0.95)
    use_llm: bool = True
    store_long_term: bool = True
    language_hint: str | None = None


class SummaryMetadata(BaseModel):
    user_id: str
    session_id: str | None = None
    source_message_count: int = Field(default=0, ge=0)
    source_token_count: int = Field(default=0, ge=0)
    summary_token_count: int = Field(default=0, ge=0)
    compression_ratio: float = Field(default=0.0, ge=0.0)
    model_name: str | None = None
    language: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConversationSummary(BaseModel):
    summary_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    session_id: str | None = None
    summary_text: str
    important_topics: list[str] = Field(default_factory=list)
    semantic_tags: list[str] = Field(default_factory=list)
    token_count: int = Field(default=0, ge=0)
    source_message_count: int = Field(default=0, ge=0)
    compression_ratio: float = Field(default=0.0, ge=0.0)
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    metadata: SummaryMetadata
    created_at: datetime = Field(default_factory=utc_now)

    @field_validator("summary_text")
    @classmethod
    def validate_summary_text(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("summary_text cannot be empty")
        return normalized
