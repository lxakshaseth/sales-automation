from typing import Any

from app.core.logger import log_error, log_event
from app.intelligence.personas.base import BasePersona
from app.intelligence.personas.exceptions import PersonaConfigurationError, PersonaValidationError
from app.intelligence.personas.formal_persona import FormalPersona
from app.intelligence.personas.models import (
    ChannelName,
    ChannelProfile,
    LanguageCode,
    LanguagePreference,
    PersonaConfig,
    PersonaContext,
    PersonaName,
    PersonaResult,
    PersonaSelection,
)
from app.intelligence.personas.multilingual_persona import MultilingualPersona
from app.intelligence.personas.sales_persona import SalesPersona
from app.intelligence.personas.support_persona import SupportPersona


class CasualPersona(SalesPersona):
    profile = SalesPersona.profile.model_copy(update={"name": PersonaName.CASUAL, "tone": "casual_conversational"})

    def apply(self, verified_response: str, *, channel_profile: ChannelProfile) -> str:
        response = self._normalize(verified_response)
        return self._truncate(response, channel_profile.max_chars)


class EnterprisePersona(FormalPersona):
    profile = FormalPersona.profile.model_copy(update={"name": PersonaName.ENTERPRISE, "tone": "enterprise_reliable"})


class PersonaManager:
    """Single source of truth for response style, language, and persona control."""

    def __init__(self, config: PersonaConfig | None = None) -> None:
        self.config = config or PersonaConfig()
        self.language_adapter = MultilingualPersona()
        self.personas: dict[PersonaName, BasePersona] = {
            PersonaName.SALES: SalesPersona(),
            PersonaName.SUPPORT: SupportPersona(),
            PersonaName.FORMAL: FormalPersona(),
            PersonaName.CASUAL: CasualPersona(),
            PersonaName.ENTERPRISE: EnterprisePersona(),
        }

    def select_persona(self, context: PersonaContext | dict[str, Any]) -> PersonaSelection:
        data = context if isinstance(context, PersonaContext) else PersonaContext(**context)
        language = self._select_language(data)
        channel_profile = self._channel_profile(data.channel)
        reasons: list[str] = []

        if data.user_preference:
            persona = data.user_preference
            reasons.append("user_preference")
        elif data.crm_type and data.crm_type.lower() in {"enterprise", "executive"}:
            persona = PersonaName.ENTERPRISE
            reasons.append("crm_requirement")
        elif data.channel == ChannelName.EMAIL:
            persona = PersonaName.FORMAL
            reasons.append("channel_email")
        elif data.channel == ChannelName.WHATSAPP:
            persona = PersonaName.CASUAL
            reasons.append("channel_whatsapp")
        elif data.conversation_stage and data.conversation_stage.lower() in {"lead_discovery", "lead_qualification", "sales"}:
            persona = PersonaName.SALES
            reasons.append("conversation_stage_sales")
        elif data.conversation_stage and data.conversation_stage.lower() in {"customer_issue", "support", "troubleshooting"}:
            persona = PersonaName.SUPPORT
            reasons.append("conversation_stage_support")
        elif data.business_workflow and "executive" in data.business_workflow.lower():
            persona = PersonaName.FORMAL
            reasons.append("business_workflow")
        else:
            persona = self.config.default_persona
            reasons.append("default_persona")

        if language.language != LanguageCode.ENGLISH:
            reasons.append("language_preference_priority")

        selection = PersonaSelection(persona=persona, language=language, channel_profile=channel_profile, reason=reasons)
        log_event("persona_selected", persona=selection.persona.value, language=selection.language.language.value, channel=data.channel.value, reasons=reasons)
        return selection

    async def apply_persona(self, context: PersonaContext | dict[str, Any]) -> PersonaResult:
        try:
            data = context if isinstance(context, PersonaContext) else PersonaContext(**context)
            selection = self.select_persona(data)
            persona = self.get_persona(selection.persona)
            styled = persona.apply(data.verified_response, channel_profile=selection.channel_profile)
            adapted = self.language_adapter.adapt_language(styled, selection.language) if self.config.allow_language_adaptation else styled
            result = PersonaResult(
                response=adapted,
                original_response=data.verified_response,
                persona=selection.persona,
                language=selection.language,
                channel=data.channel,
                modified_presentation=adapted != data.verified_response,
                facts_preserved=self.validate_persona(data.verified_response, adapted),
                metadata={"selection_reason": selection.reason, **data.metadata},
            )
            if not result.facts_preserved:
                raise PersonaValidationError("persona output may have altered verified facts")
            log_event("persona_applied", persona=result.persona.value, language=result.language.language.value, channel=result.channel.value)
            return result
        except Exception as exc:
            log_error("Persona application failed; using safe fallback persona", exc_info=True, error_type=type(exc).__name__)
            data = context if isinstance(context, PersonaContext) else PersonaContext(**context)
            language = data.language_preference or LanguagePreference(language=self.config.default_language, source="fallback")
            return PersonaResult(
                response=data.verified_response,
                original_response=data.verified_response,
                persona=self.config.fallback_persona,
                language=language,
                channel=data.channel,
                modified_presentation=False,
                facts_preserved=True,
                safety_warnings=["persona_fallback_used"],
                metadata=data.metadata,
            )

    def switch_persona(self, current: PersonaName, target: PersonaName) -> PersonaName:
        if target not in self.personas and target != PersonaName.MULTILINGUAL:
            raise PersonaConfigurationError(f"unsupported persona: {target}")
        log_event("persona_switched", from_persona=current.value, to_persona=target.value)
        return target

    def validate_persona(self, original_response: str, persona_response: str) -> bool:
        original_facts = self._fact_tokens(original_response)
        persona_facts = self._fact_tokens(persona_response)
        if not original_facts:
            return True
        if original_response.strip() in MultilingualPersona.PHRASE_MAP:
            return True
        return original_facts.issubset(persona_facts)

    def get_persona(self, persona: PersonaName | str) -> BasePersona:
        name = PersonaName(persona)
        if name == PersonaName.MULTILINGUAL:
            return self.personas[self.config.default_persona]
        selected = self.personas.get(name)
        if selected is None:
            raise PersonaConfigurationError(f"persona not configured: {name.value}")
        return selected

    def build_persona_context(self, verified_response: str, **kwargs: Any) -> PersonaContext:
        return PersonaContext(verified_response=verified_response, **kwargs)

    def _select_language(self, data: PersonaContext) -> LanguagePreference:
        if data.language_preference and data.language_preference.user_preferred:
            log_event("persona_language_preference_used", language=data.language_preference.language.value, source="user_preference")
            return data.language_preference
        if data.language_preference:
            return data.language_preference
        detected = self.language_adapter.detect_language(data.user_message or data.verified_response)
        if detected.language not in {LanguageCode.ENGLISH, LanguageCode.HINDI, LanguageCode.HINGLISH}:
            log_event("persona_language_fallback_used", detected=detected.language.value, fallback=self.config.default_language.value)
            return LanguagePreference(language=self.config.default_language, confidence=0.0, source="fallback")
        return detected

    def _channel_profile(self, channel: ChannelName) -> ChannelProfile:
        if channel == ChannelName.WHATSAPP:
            profile = ChannelProfile(channel=channel, tone="conversational", concise=True, max_chars=self.config.max_whatsapp_chars)
        elif channel == ChannelName.EMAIL:
            profile = ChannelProfile(channel=channel, tone="professional", structured=True)
        elif channel == ChannelName.CRM_NOTES:
            profile = ChannelProfile(channel=channel, tone="factual", concise=True, max_chars=500)
        elif channel == ChannelName.INTERNAL_LOGS:
            profile = ChannelProfile(channel=channel, tone="machine_readable", machine_readable=True)
        else:
            profile = ChannelProfile(channel=channel, tone="professional")
        log_event("persona_channel_adapted", channel=channel.value, tone=profile.tone, concise=profile.concise)
        return profile

    def _fact_tokens(self, text: str) -> set[str]:
        return {token.lower() for token in text.replace(".", " ").replace(",", " ").split() if any(char.isdigit() for char in token) or token[:1].isupper()}


async def apply_persona(context: PersonaContext | dict[str, Any]) -> PersonaResult:
    return await PersonaManager().apply_persona(context)
