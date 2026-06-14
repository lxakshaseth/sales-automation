from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictPersonaModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class PersonaName(StrEnum):
    SALES = "sales"
    SUPPORT = "support"
    FORMAL = "formal"
    CASUAL = "casual"
    ENTERPRISE = "enterprise"
    MULTILINGUAL = "multilingual"


class LanguageCode(StrEnum):
    ENGLISH = "en"
    HINDI = "hi"
    HINGLISH = "hinglish"


class ChannelName(StrEnum):
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    CRM_NOTES = "crm_notes"
    INTERNAL_LOGS = "internal_logs"
    DEFAULT = "default"


class PersonaConfig(StrictPersonaModel):
    default_persona: PersonaName = PersonaName.ENTERPRISE
    fallback_persona: PersonaName = PersonaName.FORMAL
    default_language: LanguageCode = LanguageCode.ENGLISH
    allow_language_adaptation: bool = True
    preserve_verified_facts: bool = True
    max_whatsapp_chars: int = Field(default=320, ge=80)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("default_persona", "fallback_persona", mode="before")
    @classmethod
    def parse_persona_name(cls, value: PersonaName | str) -> PersonaName:
        return value if isinstance(value, PersonaName) else PersonaName(str(value))

    @field_validator("default_language", mode="before")
    @classmethod
    def parse_default_language(cls, value: LanguageCode | str) -> LanguageCode:
        return value if isinstance(value, LanguageCode) else LanguageCode(str(value))


class PersonaProfile(StrictPersonaModel):
    name: PersonaName
    description: str
    tone: str
    style_rules: list[str] = Field(default_factory=list)
    safety_rules: list[str] = Field(default_factory=list)
    supported_channels: list[ChannelName] = Field(default_factory=lambda: [ChannelName.DEFAULT])


class LanguagePreference(StrictPersonaModel):
    language: LanguageCode = LanguageCode.ENGLISH
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source: str = "fallback"
    user_preferred: bool = False

    @field_validator("language", mode="before")
    @classmethod
    def parse_language(cls, value: LanguageCode | str) -> LanguageCode:
        return value if isinstance(value, LanguageCode) else LanguageCode(str(value))


class ChannelProfile(StrictPersonaModel):
    channel: ChannelName = ChannelName.DEFAULT
    tone: str = "professional"
    concise: bool = False
    structured: bool = False
    machine_readable: bool = False
    max_chars: int | None = Field(default=None, ge=1)

    @field_validator("channel", mode="before")
    @classmethod
    def parse_channel(cls, value: ChannelName | str) -> ChannelName:
        return value if isinstance(value, ChannelName) else ChannelName(str(value))


class PersonaContext(StrictPersonaModel):
    verified_response: str
    user_message: str | None = None
    user_preference: PersonaName | None = None
    language_preference: LanguagePreference | None = None
    channel: ChannelName = ChannelName.DEFAULT
    crm_type: str | None = None
    conversation_stage: str | None = None
    business_workflow: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("user_preference", mode="before")
    @classmethod
    def parse_user_preference(cls, value: PersonaName | str | None) -> PersonaName | None:
        if value is None:
            return None
        return value if isinstance(value, PersonaName) else PersonaName(str(value))

    @field_validator("channel", mode="before")
    @classmethod
    def parse_context_channel(cls, value: ChannelName | str) -> ChannelName:
        return value if isinstance(value, ChannelName) else ChannelName(str(value))

    @field_validator("verified_response")
    @classmethod
    def validate_verified_response(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("verified_response cannot be empty")
        return normalized


class PersonaSelection(StrictPersonaModel):
    persona: PersonaName
    language: LanguagePreference
    channel_profile: ChannelProfile
    reason: list[str] = Field(default_factory=list)


class PersonaResult(StrictPersonaModel):
    response: str
    original_response: str
    persona: PersonaName
    language: LanguagePreference
    channel: ChannelName
    modified_presentation: bool = False
    facts_preserved: bool = True
    safety_warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("response")
    @classmethod
    def validate_response(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("persona response cannot be empty")
        return normalized
