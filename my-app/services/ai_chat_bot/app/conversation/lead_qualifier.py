import re

from app.conversation.models import ConversationIntent, ConversationState, LeadStage


class LeadQualifier:
    """Maintains lightweight lead qualification state across messages."""

    LANGUAGE_ALIASES = {
        "english": "en",
        "hindi": "hi",
        "hinglish": "hinglish",
        "urdu": "ur",
        "french": "fr",
        "spanish": "es",
        "german": "de",
        "marathi": "mr",
        "\u0939\u093f\u0902\u0926\u0940": "hi",
        "\u0627\u0631\u062f\u0648": "ur",
    }

    def update(self, state: ConversationState, message: str, intent: ConversationIntent) -> ConversationState:
        text = str(message or "").strip()
        lower = text.lower()

        if intent == ConversationIntent.LANGUAGE_SWITCH:
            for alias, code in self.LANGUAGE_ALIASES.items():
                if alias in lower:
                    state.preferred_language = code
                    break
            state.previous_intent = intent
            return state

        if intent in {ConversationIntent.SERVICE_INQUIRY, ConversationIntent.PRODUCT_INQUIRY, ConversationIntent.LEAD_QUALIFICATION}:
            state.lead.interest = state.lead.interest or text
            state.stage = "qualifying"
            if state.lead_stage == LeadStage.UNKNOWN:
                state.lead_stage = LeadStage.DISCOVERY

        if "switch to hindi" in lower or "hindi" in lower and any(term in lower for term in ("speak", "talk", "switch")):
            state.preferred_language = "hi"
        elif "hinglish" in lower:
            state.preferred_language = "hinglish"
        elif "switch to english" in lower or "english" in lower and "switch" in lower:
            state.preferred_language = "en"

        business_match = re.search(r"\b(?:my company|our company|my business|our business|we)\s+(?:works?|operate|operates|are|is)\s+(?:in|within)?\s*(?:the\s+)?([a-z][a-z\s-]{2,40}?)(?:\s+sector|\s+industry|\.|$)", lower)
        if business_match:
            industry = business_match.group(1).strip(" .")
            state.lead.industry = state.lead.industry or industry
            state.lead.business_type = state.lead.business_type or industry
            state.stage = "qualifying"
            if state.lead_stage == LeadStage.UNKNOWN:
                state.lead_stage = LeadStage.DISCOVERY

        if "beauty" in lower:
            state.lead.industry = state.lead.industry or "beauty"
            state.lead.business_type = state.lead.business_type or "beauty"

        email = re.search(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", text, re.IGNORECASE)
        if email:
            state.lead.email = email.group(0)

        phone = re.search(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)", text)
        if phone:
            state.lead.phone = phone.group(0)

        if any(term in lower for term in ("month", "monthly", "customers", "inquiries", "enquiries")):
            state.lead.monthly_volume = text
            state.stage = "qualified_volume"
            state.lead_stage = LeadStage.QUALIFIED

        if any(term in lower for term in ("urgent", "this week", "this month", "next month", "soon")):
            state.lead.timeline = text
            if state.lead_stage == LeadStage.UNKNOWN:
                state.lead_stage = LeadStage.DISCOVERY

        if any(term in lower for term in ("budget", "$", "usd", "inr", "rs", "lakh")):
            state.lead.budget = text

        if any(term in lower for term in ("team", "employees", "staff", "people")):
            state.lead.team_size = text

        state.previous_intent = intent
        return state

    def next_question(self, state: ConversationState) -> str:
        if not state.lead.business_type and not state.lead.industry and not state.lead.interest:
            return "Could you tell me what kind of business you run?"
        if not state.lead.monthly_volume:
            if state.lead.industry:
                return f"That's great. How many customer inquiries does your {state.lead.industry} business typically receive each month?"
            return "Could you tell me how many customer inquiries you handle each month?"
        if not state.lead.team_size:
            return "How many people are currently on your sales or customer support team?"
        if not state.lead.timeline:
            return "What timeline are you considering for launching this?"
        if not state.lead.budget:
            return "Do you have a budget range in mind, or should I suggest options based on your needs?"
        return "Would you like to book a quick demo so we can recommend the right setup?"
