from app.intelligence.personas.base import BasePersona
from app.intelligence.personas.models import ChannelName, ChannelProfile, PersonaName, PersonaProfile


class SalesPersona(BasePersona):
    profile = PersonaProfile(
        name=PersonaName.SALES,
        description="Professional, value-focused sales persona.",
        tone="persuasive_professional",
        style_rules=["encourage engagement", "highlight verified benefits", "suggest next action"],
        safety_rules=["do not fabricate urgency", "do not make false promises", "do not alter verified facts"],
        supported_channels=[ChannelName.WHATSAPP, ChannelName.EMAIL, ChannelName.DEFAULT],
    )

    def apply(self, verified_response: str, *, channel_profile: ChannelProfile) -> str:
        response = self._normalize(verified_response)
        if channel_profile.channel == ChannelName.WHATSAPP:
            if not response.endswith("?") and "next" not in response.lower():
                response = f"{response} Would you like me to help with the next step?"
            return self._truncate(response, channel_profile.max_chars)
        if channel_profile.channel == ChannelName.EMAIL:
            return f"{response}\n\nRecommended next step: please confirm how you would like to proceed."
        return response
