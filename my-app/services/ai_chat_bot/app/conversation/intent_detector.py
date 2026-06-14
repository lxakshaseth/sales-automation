from app.conversation.models import ConversationIntent, IntentResult


class IntentDetector:
    """Lightweight deterministic intent detector for short WhatsApp sales messages."""

    ABUSE_TERMS = {"fuck", "fuck off", "stupid", "idiot", "moron", "dumb"}
    LANGUAGE_NAMES = {
        "english",
        "hindi",
        "hinglish",
        "urdu",
        "french",
        "spanish",
        "german",
        "marathi",
        "\u0939\u093f\u0902\u0926\u0940",
        "\u0627\u0631\u062f\u0648",
    }
    LANGUAGE_TERMS = {
        *LANGUAGE_NAMES,
        "switch language",
        "change language",
        "switch to english",
        "switch to hindi",
        "switch to hinglish",
        "switch to urdu",
        "switch to french",
        "talk in english",
        "talk in hindi",
        "talk in urdu",
        "talk in french",
        "reply in english",
        "reply in hindi",
        "reply in urdu",
        "reply in french",
        "continue in english",
        "continue in hindi",
        "continue in urdu",
        "continue in french",
    }

    def detect(self, message: str) -> IntentResult:
        text = " ".join(str(message or "").strip().lower().split())
        if not text:
            return IntentResult(ConversationIntent.UNKNOWN, 0.0, "empty")

        if any(term in text for term in self.ABUSE_TERMS):
            return IntentResult(ConversationIntent.ABUSE, 0.95, "abuse_keyword")
        if text in self.LANGUAGE_NAMES:
            return IntentResult(ConversationIntent.LANGUAGE_SWITCH, 0.99, "language_name")
        if any(term in text for term in self.LANGUAGE_TERMS):
            return IntentResult(ConversationIntent.LANGUAGE_SWITCH, 0.96, "language_switch_keyword")
        if text in {"hi", "hii", "hello", "hey", "good morning", "good evening"}:
            return IntentResult(ConversationIntent.GREETING, 0.99, "greeting_keyword")
        if text in {"thanks", "thank you", "bye", "goodbye"} or "how are you" in text:
            return IntentResult(ConversationIntent.SMALL_TALK, 0.90, "small_talk_keyword")
        if any(term in text for term in ("service", "services", "sales automation", "automation service")):
            return IntentResult(ConversationIntent.SERVICE_INQUIRY, 0.92, "service_keyword")
        if any(term in text for term in ("product", "platform", "software", "solution")):
            return IntentResult(ConversationIntent.PRODUCT_INQUIRY, 0.88, "product_keyword")
        if any(term in text for term in ("price", "pricing", "cost", "budget", "quote", "daam", "keemat", "kimat", "\u092a\u094d\u0930\u093e\u0907\u0938", "\u092a\u094d\u0930\u093e\u0907\u0938\u093f\u0902\u0917", "\u0915\u0940\u092e\u0924")):
            return IntentResult(ConversationIntent.PRICING_REQUEST, 0.90, "pricing_keyword")
        if "demo" in text:
            return IntentResult(ConversationIntent.DEMO_REQUEST, 0.94, "demo_keyword")
        if any(term in text for term in ("meeting", "appointment", "schedule", "call")):
            return IntentResult(ConversationIntent.MEETING_REQUEST, 0.90, "meeting_keyword")
        if any(term in text for term in ("support", "help", "issue", "problem")):
            return IntentResult(ConversationIntent.SUPPORT_REQUEST, 0.82, "support_keyword")
        if any(term in text for term in ("chatbot", "bot", "lead", "customers", "inquiries", "enquiries")):
            return IntentResult(ConversationIntent.LEAD_QUALIFICATION, 0.84, "lead_qualification_keyword")
        if any(term in text for term in ("explain", "what is", "what are", "tell me about", "how does", "why does")):
            return IntentResult(ConversationIntent.GENERAL_CONVERSATION, 0.72, "general_question")
        return IntentResult(ConversationIntent.UNKNOWN, 0.45, "no_keyword_match")
