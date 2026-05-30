from app.intelligence.personas.base import BasePersona
from app.intelligence.personas.models import ChannelName, ChannelProfile, PersonaName, PersonaProfile


class FormalPersona(BasePersona):
    profile = PersonaProfile(
        name=PersonaName.FORMAL,
        description="Formal, concise, executive-ready persona.",
        tone="formal_business",
        style_rules=["use professional language", "keep concise", "structure for business readers"],
        safety_rules=["do not add unverified details", "do not change facts"],
        supported_channels=[ChannelName.EMAIL, ChannelName.CRM_NOTES, ChannelName.INTERNAL_LOGS, ChannelName.DEFAULT],
    )

    def apply(self, verified_response: str, *, channel_profile: ChannelProfile) -> str:
        response = self._normalize(verified_response)
        if channel_profile.channel == ChannelName.CRM_NOTES:
            return self._truncate(f"Note: {response}", channel_profile.max_chars)
        if channel_profile.channel == ChannelName.INTERNAL_LOGS:
            return response
        if channel_profile.structured:
            return f"Hello,\n\n{response}\n\nRegards,"
        return response
