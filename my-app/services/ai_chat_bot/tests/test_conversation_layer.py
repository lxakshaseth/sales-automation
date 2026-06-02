import asyncio

from app.conversation import ConversationIntent, ConversationService, IntentDetector, LeadStage
from app.intelligence.orchestration.models import ExecutionTrace, OrchestrationResponse, ReasoningMode, RequestType
from app.security.orchestrator import SecurityOrchestrator


class FakeAIOrchestrator:
    def __init__(self, response_text: str) -> None:
        self.response_text = response_text
        self.calls = []

    async def process_request(self, request):
        self.calls.append(request)
        return OrchestrationResponse(
            success=True,
            response=self.response_text,
            raw_response=self.response_text,
            request_type=RequestType.CHAT,
            reasoning_mode=ReasoningMode.SIMPLE_REPLY,
            confidence=0.25,
            action="fallback_response",
            traces=[ExecutionTrace(step="fake_groq", status="success")],
            metadata={"model_provider": "fake_groq"},
        )


def run(coro):
    return asyncio.run(coro)


def test_intent_detection_short_messages():
    detector = IntentDetector()

    assert detector.detect("hi").intent == ConversationIntent.GREETING
    assert detector.detect("service").intent == ConversationIntent.SERVICE_INQUIRY
    assert detector.detect("product").intent == ConversationIntent.PRODUCT_INQUIRY
    assert detector.detect("meeting").intent == ConversationIntent.MEETING_REQUEST
    assert detector.detect("price").intent == ConversationIntent.PRICING_REQUEST
    assert detector.detect("demo").intent == ConversationIntent.DEMO_REQUEST
    assert detector.detect("fuck off").intent == ConversationIntent.ABUSE
    assert detector.detect("can we switch language").intent == ConversationIntent.LANGUAGE_SWITCH
    assert detector.detect("hindi").intent == ConversationIntent.LANGUAGE_SWITCH


def test_greeting_response_is_natural():
    security = SecurityOrchestrator()

    response = run(security.process_request({"user_query": "hi", "tenant_id": "tenant_A", "session_id": "greeting"}))

    assert response.success is True
    assert response.action == "conversation_response"
    assert response.response.startswith("Hello! Welcome.")
    assert "How can I assist you today?" in response.response
    assert response.metadata["intent"] == "GREETING"
    assert response.metrics.hallucination_risk == "SKIPPED_CONVERSATION"


def test_service_inquiry_explains_services():
    security = SecurityOrchestrator()

    response = run(security.process_request({"user_query": "service", "tenant_id": "tenant_A", "session_id": "service"}))

    assert response.success is True
    assert "AI Chatbot Solutions" in response.response
    assert "WhatsApp Automation" in response.response
    assert "Which service would you like to know more about?" in response.response


def test_product_inquiry_asks_followup():
    service = ConversationService()

    result = service.handle_message(message="product", tenant_id="tenant_A", user_id="user-product")

    assert result.intent == ConversationIntent.PRODUCT_INQUIRY
    assert "which product" in result.response.lower()
    assert "problem you're trying to solve" in result.response


def test_meeting_request_collects_details():
    security = SecurityOrchestrator()

    response = run(security.process_request({"user_query": "meeting", "tenant_id": "tenant_A", "session_id": "meeting"}))

    assert response.success is True
    assert "Your name" in response.response
    assert "Company name" in response.response
    assert "Preferred date and time" in response.response


def test_support_request_keeps_conversation_moving():
    service = ConversationService()

    result = service.handle_message(message="I need help", tenant_id="tenant_A", user_id="user-help")

    assert result.intent == ConversationIntent.SUPPORT_REQUEST
    assert "I can help" in result.response
    assert "technical support" in result.response


def test_lead_qualification_and_memory_continue_stage():
    service = ConversationService()

    first = service.handle_message(message="I need a chatbot", tenant_id="tenant_A", user_id="lead-1")
    second = service.handle_message(message="We receive 500 inquiries monthly", tenant_id="tenant_A", user_id="lead-1")
    state = service.get_state(tenant_id="tenant_A", user_id="lead-1")

    assert first.intent == ConversationIntent.LEAD_QUALIFICATION
    assert "how many customers" in first.response
    assert second.stage == "qualified_volume"
    assert state.lead.interest == "I need a chatbot"
    assert state.lead.monthly_volume == "We receive 500 inquiries monthly"
    assert "How many people" in second.response


def test_abuse_escalates_professionally():
    security = SecurityOrchestrator()
    payload = {"user_query": "fuck off", "tenant_id": "tenant_A", "session_id": "abuse-session"}

    first = run(security.process_request(payload))
    second = run(security.process_request(payload))
    third = run(security.process_request(payload))

    assert first.response == "I'd appreciate respectful communication.\n\nI'm here to assist with products, services, pricing, demos, and support."
    assert second.response == "Warning: Please keep the conversation professional so I can assist you effectively."
    assert third.response == "Conversation temporarily restricted due to repeated inappropriate language."


def test_groq_fallback_replaces_strict_rag_failure():
    fake_ai = FakeAIOrchestrator("The available data is insufficient to provide a reliable answer.")
    security = SecurityOrchestrator(ai_orchestrator=fake_ai)

    response = run(
        security.process_request(
            {
                "user_query": "Please follow up with this lead about chatbot",
                "tenant_id": "tenant_A",
                "session_id": "groq-fallback",
            }
        )
    )

    assert fake_ai.calls
    assert response.success is True
    assert response.action == "conversation_fallback"
    assert "available data is insufficient" not in response.response.lower()
    assert "Could you tell me a little about your business" in response.response
    assert response.metadata["fallback_reason"] == "conversation_layer_replaced_low_confidence_response"


def test_unknown_short_message_asks_clarifying_question():
    service = ConversationService()

    result = service.handle_message(message="laptop", tenant_id="tenant_A", user_id="unknown-1")

    assert result.intent == ConversationIntent.UNKNOWN
    assert "looking for in laptop" in result.response
    assert "Budget" in result.response


def test_beauty_business_is_remembered_and_not_requalified():
    service = ConversationService()

    first = service.handle_message(message="My company works in beauty sector", tenant_id="tenant_A", user_id="beauty-1")
    second = service.handle_message(message="What business do I work in?", tenant_id="tenant_A", user_id="beauty-1")
    third = service.handle_message(message="hi", tenant_id="tenant_A", user_id="beauty-1")
    state = service.get_state(tenant_id="tenant_A", user_id="beauty-1")

    assert state.lead.industry == "beauty"
    assert state.lead_stage == LeadStage.DISCOVERY
    assert "customer inquiries" in first.response
    assert second.response == "You mentioned your company operates in the beauty sector."
    assert third.response == "Welcome back. We were discussing your beauty business. Would you like to continue?"


def test_language_preference_persists_in_conversation_state():
    service = ConversationService()

    first = service.handle_message(message="Can we switch to Hindi?", tenant_id="tenant_A", user_id="lang-1")
    second = service.handle_message(message="service", tenant_id="tenant_A", user_id="lang-1")
    state = service.get_state(tenant_id="tenant_A", user_id="lang-1")

    assert state.preferred_language == "hi"
    assert "\u0939\u093f\u0902\u0926\u0940" in first.response
    assert second.metadata["preferred_language"] == "hi"


def test_language_switch_request_asks_target_language():
    service = ConversationService()

    result = service.handle_message(message="can we switch language", tenant_id="tenant_A", user_id="lang-ask")

    assert result.intent == ConversationIntent.LANGUAGE_SWITCH
    assert result.response == "Sure. Which language would you like to continue in?"


def test_hindi_message_switches_language_immediately():
    service = ConversationService()

    result = service.handle_message(message="hindi", tenant_id="tenant_A", user_id="lang-hindi")
    state = service.get_state(tenant_id="tenant_A", user_id="lang-hindi")

    assert result.intent == ConversationIntent.LANGUAGE_SWITCH
    assert state.preferred_language == "hi"
    assert "\u0939\u093f\u0902\u0926\u0940" in result.response
    assert "Budget" not in result.response


def test_hindi_pricing_response_respects_language():
    service = ConversationService()

    service.handle_message(message="hindi", tenant_id="tenant_A", user_id="pricing-hi")
    result = service.handle_message(message="\u092e\u0941\u091d\u0947 \u092a\u094d\u0930\u093e\u0907\u0938\u093f\u0902\u0917 \u091c\u093e\u0928\u0928\u0940 \u0939\u0948", tenant_id="tenant_A", user_id="pricing-hi")

    assert result.intent == ConversationIntent.PRICING_REQUEST
    assert "\u092a\u094d\u0930\u093e\u0907\u0938\u093f\u0902\u0917" in result.response
    assert result.metadata["preferred_language"] == "hi"


def test_general_conversation_routes_to_groq_fallback():
    fake_ai = FakeAIOrchestrator("Artificial general intelligence is a broad AI capability. For your business, I can relate it to automation use cases.")
    security = SecurityOrchestrator(ai_orchestrator=fake_ai)

    response = run(
        security.process_request(
            {
                "user_query": "Explain artificial general intelligence",
                "tenant_id": "tenant_A",
                "session_id": "general-groq",
            }
        )
    )

    assert fake_ai.calls
    assert response.success is True
    assert response.response.startswith("Artificial general intelligence")


def test_solution_recommendation_uses_beauty_context():
    service = ConversationService()

    service.handle_message(message="My company works in beauty industry", tenant_id="tenant_A", user_id="beauty-solution")
    result = service.handle_message(message="What solution do you recommend?", tenant_id="tenant_A", user_id="beauty-solution")

    assert result.intent in {ConversationIntent.PRODUCT_INQUIRY, ConversationIntent.GENERAL_CONVERSATION, ConversationIntent.UNKNOWN}
    assert result.should_respond_directly is True
    assert "beauty business" in result.response
    assert "AI WhatsApp chatbot" in result.response
    state = service.get_state(tenant_id="tenant_A", user_id="beauty-solution")
    assert state.lead.business_type == "beauty"


def test_lead_stage_reaches_qualified_after_volume():
    service = ConversationService()

    service.handle_message(message="My company works in beauty sector", tenant_id="tenant_A", user_id="stage-1")
    result = service.handle_message(message="We receive 500 inquiries monthly", tenant_id="tenant_A", user_id="stage-1")
    state = service.get_state(tenant_id="tenant_A", user_id="stage-1")

    assert state.lead_stage == LeadStage.QUALIFIED
    assert result.metadata["lead_stage"] == "QUALIFIED"
    assert "How many people" in result.response
