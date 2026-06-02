from app.conversation.models import ConversationIntent, ConversationState


class DialoguePolicy:
    """Maps sales intents to professional conversational responses."""

    LANGUAGE_CONFIRMATIONS = {
        "en": [
            "Sure, I will continue in English. How can I help you today?",
            "Absolutely, English it is. What would you like to discuss?",
        ],
        "hi": [
            "\u091c\u093c\u0930\u0942\u0930. \u0905\u092c \u092e\u0948\u0902 \u0939\u093f\u0902\u0926\u0940 \u092e\u0947\u0902 \u092c\u093e\u0924 \u0915\u0930\u0942\u0902\u0917\u093e. \u092e\u0948\u0902 \u0906\u092a\u0915\u0940 \u0915\u093f\u0938 \u092a\u094d\u0930\u0915\u093e\u0930 \u0938\u0939\u093e\u092f\u0924\u093e \u0915\u0930 \u0938\u0915\u0924\u093e \u0939\u0942\u0902?",
            "\u092c\u093f\u0932\u094d\u0915\u0941\u0932, \u0905\u092c \u0939\u092e \u0939\u093f\u0902\u0926\u0940 \u092e\u0947\u0902 \u092c\u093e\u0924 \u0915\u0930\u0947\u0902\u0917\u0947. \u0906\u092a\u0915\u094b \u0915\u093f\u0938 \u091a\u0940\u091c\u093c \u092e\u0947\u0902 \u092e\u0926\u0926 \u091a\u093e\u0939\u093f\u090f?",
        ],
        "hinglish": [
            "Sure, ab main Hinglish mein baat karunga. Aapko services, pricing, demo, ya support mein kis cheez ki help chahiye?",
            "Bilkul, Hinglish mein continue karte hain. Aap apni requirement bata sakte hain?",
        ],
        "ur": [
            "\u0636\u0631\u0648\u0631\u060c \u0627\u0628 \u0645\u06cc\u06ba \u0627\u0631\u062f\u0648 \u0645\u06cc\u06ba \u0628\u0627\u062a \u06a9\u0631\u0648\u06ba \u06af\u0627\u06d4 \u0622\u067e \u06a9\u0648 \u06a9\u0633 \u0686\u06cc\u0632 \u0645\u06cc\u06ba \u0645\u062f\u062f \u0686\u0627\u06c1\u06cc\u06d2\u061f",
            "\u0628\u0627\u0644\u06a9\u0644\u060c \u0627\u0631\u062f\u0648 \u0645\u06cc\u06ba \u0628\u0627\u062a \u06a9\u0631\u062a\u06d2 \u06c1\u06cc\u06ba\u06d4 \u0622\u067e \u0627\u067e\u0646\u06cc \u0636\u0631\u0648\u0631\u062a \u0628\u062a\u0627 \u0633\u06a9\u062a\u06d2 \u06c1\u06cc\u06ba\u061f",
        ],
        "fr": [
            "Bien sur, je vais continuer en francais. Comment puis-je vous aider ?",
            "D'accord, continuons en francais. Quel type d'aide recherchez-vous ?",
        ],
        "es": [
            "Claro, continuare en espanol. Como puedo ayudarte?",
            "Perfecto, seguimos en espanol. Que necesitas saber?",
        ],
        "de": [
            "Gerne, ich antworte ab jetzt auf Deutsch. Wie kann ich helfen?",
            "Alles klar, wir machen auf Deutsch weiter. Wobei kann ich helfen?",
        ],
        "mr": [
            "\u0928\u0915\u094d\u0915\u0940, \u0906\u0924\u093e \u092e\u0940 \u092e\u0930\u093e\u0920\u0940\u0924 \u092c\u094b\u0932\u0947\u0928. \u0924\u0941\u092e\u094d\u0939\u093e\u0932\u093e \u0915\u0936\u093e\u0924 \u092e\u0926\u0924 \u0939\u0935\u0940 \u0906\u0939\u0947?",
        ],
    }

    GREETINGS = [
        "Hello, welcome. How can I help you today?",
        "Hi, thanks for reaching out. What would you like to explore today?",
        "Hello. I can help with services, pricing, demos, or support. What are you looking for?",
    ]

    UNKNOWN_SHORT_REPLIES = [
        "Sure, I can help with that. Could you share a little more about what you need?",
        "Got it. Are you looking for details, pricing, a demo, or support?",
        "Happy to help. Could you tell me the goal behind this request?",
    ]

    def response_for(self, intent: ConversationIntent, message: str, state: ConversationState) -> str:
        normalized = " ".join(str(message or "").strip().lower().split())

        if intent == ConversationIntent.LANGUAGE_SWITCH:
            responses = self.LANGUAGE_CONFIRMATIONS.get(state.preferred_language)
            if responses:
                return self._pick(responses, state)
            return "Sure. Which language would you like to continue in?"

        if intent == ConversationIntent.GREETING:
            return self._pick(self.GREETINGS, state)

        if intent == ConversationIntent.SMALL_TALK:
            if normalized in {"bye", "goodbye"}:
                return "Thanks for chatting. If you need help with products, services, pricing, or demos, I am here."
            if normalized in {"thanks", "thank you"}:
                return "You're welcome. Would you like details about our services, pricing, or a demo?"
            return "I'm doing well and ready to help. Are you looking for products, services, pricing, a demo, or support?"

        if intent == ConversationIntent.SERVICE_INQUIRY:
            return (
                "We offer several services including:\n\n"
                "- AI Chatbot Solutions\n"
                "- WhatsApp Automation\n"
                "- Sales Automation\n"
                "- Lead Management\n"
                "- Customer Engagement\n\n"
                "Which service would you like to know more about?"
            )

        if intent == ConversationIntent.PRODUCT_INQUIRY:
            return (
                "I'd be happy to help.\n\n"
                "Could you tell me which product you're interested in or what problem you're trying to solve?"
            )

        if intent == ConversationIntent.MEETING_REQUEST:
            return (
                "Certainly.\n\n"
                "I'd be happy to arrange a meeting.\n\n"
                "Could you share:\n\n"
                "- Your name\n"
                "- Company name\n"
                "- Preferred date and time\n\n"
                "and I'll help schedule it."
            )

        if intent == ConversationIntent.PRICING_REQUEST:
            if state.preferred_language == "hi":
                return "\u092a\u094d\u0930\u093e\u0907\u0938\u093f\u0902\u0917 \u0906\u092a\u0915\u0947 use case, message volume, \u0914\u0930 automation needs \u092a\u0930 depend \u0915\u0930\u0924\u0940 \u0939\u0948. \u0906\u092a \u092c\u0924\u093e \u0938\u0915\u0924\u0947 \u0939\u0948\u0902 \u0915\u093f \u0906\u092a \u0915\u094d\u092f\u093e automate \u0915\u0930\u0928\u093e \u091a\u093e\u0939\u0924\u0947 \u0939\u0948\u0902 \u0914\u0930 monthly \u0915\u093f\u0924\u0928\u0940 customer conversations handle \u0915\u0930\u0924\u0947 \u0939\u0948\u0902?"
            if state.preferred_language == "hinglish":
                return "Pricing aapke use case, message volume, aur automation needs par depend karti hai. Aap kya automate karna chahte hain aur monthly kitni customer conversations handle karte hain?"
            return (
                "Pricing depends on your use case, message volume, and automation needs.\n\n"
                "Could you share what you want to automate and roughly how many customer conversations you handle each month?"
            )

        if intent == ConversationIntent.DEMO_REQUEST:
            return (
                "Absolutely. I can help arrange a demo.\n\n"
                "Could you share your name, company, and a preferred time?"
            )

        if intent == ConversationIntent.SUPPORT_REQUEST:
            return "Sure, I can help. Are you looking for product information, service details, pricing, a demo, or technical support?"

        if intent == ConversationIntent.LEAD_QUALIFICATION:
            return "Great.\n\nCould you tell me a little about your business and how many customers you interact with each month?"

        if intent == ConversationIntent.GENERAL_CONVERSATION:
            return "I can help with that. Let me give you a clear answer and relate it to your business needs where useful."

        if normalized and len(normalized.split()) <= 3:
            return self._pick(self.UNKNOWN_SHORT_REPLIES, state)

        return (
            "I can help with that. Could you share a little more context so I can guide you properly?"
        )

    def _pick(self, responses: list[str], state: ConversationState) -> str:
        return responses[state.response_variant % len(responses)]
