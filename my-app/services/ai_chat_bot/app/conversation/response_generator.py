from app.conversation.dialogue_policy import DialoguePolicy
from app.conversation.lead_qualifier import LeadQualifier
from app.conversation.models import ConversationIntent, ConversationState


class ResponseGenerator:
    def __init__(self, dialogue_policy: DialoguePolicy | None = None, lead_qualifier: LeadQualifier | None = None) -> None:
        self.dialogue_policy = dialogue_policy or DialoguePolicy()
        self.lead_qualifier = lead_qualifier or LeadQualifier()

    def generate(self, intent: ConversationIntent, message: str, state: ConversationState) -> str:
        lower = str(message or "").strip().lower()
        if any(term in lower for term in ("recommend", "suggest", "right solution")) and state.lead.industry:
            return (
                f"For your {state.lead.industry} business, I would recommend an AI WhatsApp chatbot that can answer FAQs, "
                "capture leads, qualify customer needs, and hand over serious inquiries to your sales team. "
                "How many customer inquiries do you usually receive each month?"
            )
        if ("what business" in lower or "which business" in lower or "what industry" in lower) and state.lead.industry:
            return f"You mentioned your company operates in the {state.lead.industry} sector."
        if intent == ConversationIntent.GREETING and state.lead.industry:
            return f"Welcome back. We were discussing your {state.lead.industry} business. Would you like to continue?"
        if state.stage == "qualified_volume":
            return self.lead_qualifier.next_question(state)
        if state.stage == "qualifying" and intent == ConversationIntent.UNKNOWN:
            return self.lead_qualifier.next_question(state)
        return self.dialogue_policy.response_for(intent, message, state)
