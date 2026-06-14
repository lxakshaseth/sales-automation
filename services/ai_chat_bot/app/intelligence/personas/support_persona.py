from app.intelligence.personas.base import BasePersona
from app.intelligence.personas.models import ChannelName, ChannelProfile, PersonaName, PersonaProfile


class SupportPersona(BasePersona):
    profile = PersonaProfile(
        name=PersonaName.SUPPORT,
        description="Helpful, patient, solution-oriented support persona.",
        tone="empathetic_clear",
        style_rules=["clarify issue", "guide safely", "use step-by-step language"],
        safety_rules=["do not guarantee outcomes", "do not invent diagnostics", "do not alter verified facts"],
        supported_channels=[ChannelName.WHATSAPP, ChannelName.EMAIL, ChannelName.DEFAULT],
    )

    def apply(self, verified_response: str, *, channel_profile: ChannelProfile) -> str:
        response = self._normalize(verified_response)
        if channel_profile.channel == ChannelName.WHATSAPP:
            return self._truncate(f"I understand. {response}", channel_profile.max_chars)
        if channel_profile.channel == ChannelName.EMAIL:
            return f"Thank you for the details.\n\n{response}\n\nPlease let me know if you would like me to clarify any part of this."
        return response
