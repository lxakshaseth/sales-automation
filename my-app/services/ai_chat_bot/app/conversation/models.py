from dataclasses import dataclass, field
from enum import StrEnum


class ConversationIntent(StrEnum):
    LANGUAGE_SWITCH = "LANGUAGE_SWITCH"
    GREETING = "GREETING"
    SMALL_TALK = "SMALL_TALK"
    PRODUCT_INQUIRY = "PRODUCT_INQUIRY"
    SERVICE_INQUIRY = "SERVICE_INQUIRY"
    PRICING_REQUEST = "PRICING_REQUEST"
    DEMO_REQUEST = "DEMO_REQUEST"
    MEETING_REQUEST = "MEETING_REQUEST"
    SUPPORT_REQUEST = "SUPPORT_REQUEST"
    LEAD_QUALIFICATION = "LEAD_QUALIFICATION"
    GENERAL_CONVERSATION = "GENERAL_CONVERSATION"
    ABUSE = "ABUSE"
    UNKNOWN = "UNKNOWN"


class LeadStage(StrEnum):
    UNKNOWN = "UNKNOWN"
    DISCOVERY = "DISCOVERY"
    QUALIFIED = "QUALIFIED"
    DEMO = "DEMO"
    FOLLOWUP = "FOLLOWUP"
    CLOSED = "CLOSED"


@dataclass
class LeadProfile:
    name: str | None = None
    company: str | None = None
    phone: str | None = None
    email: str | None = None
    interest: str | None = None
    business_type: str | None = None
    industry: str | None = None
    team_size: str | None = None
    pain_points: list[str] = field(default_factory=list)
    budget: str | None = None
    timeline: str | None = None
    monthly_volume: str | None = None


@dataclass
class ConversationState:
    tenant_id: str
    user_id: str
    previous_intent: ConversationIntent | None = None
    stage: str = "start"
    lead_stage: LeadStage = LeadStage.UNKNOWN
    preferred_language: str = "en"
    response_variant: int = 0
    lead: LeadProfile = field(default_factory=LeadProfile)


@dataclass
class IntentResult:
    intent: ConversationIntent
    confidence: float
    reason: str


@dataclass
class ConversationResult:
    response: str
    intent: ConversationIntent
    confidence: float = 1.0
    should_respond_directly: bool = True
    stage: str = "conversation"
    metadata: dict[str, object] = field(default_factory=dict)
