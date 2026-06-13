from app.conversation.intent_detector import IntentDetector
from app.conversation.lead_qualifier import LeadQualifier
from app.conversation.models import ConversationIntent, ConversationResult, ConversationState
from app.conversation.response_generator import ResponseGenerator


class ConversationManager:
    def __init__(
        self,
        *,
        intent_detector: IntentDetector | None = None,
        lead_qualifier: LeadQualifier | None = None,
        response_generator: ResponseGenerator | None = None,
    ) -> None:
        self.intent_detector = intent_detector or IntentDetector()
        self.lead_qualifier = lead_qualifier or LeadQualifier()
        self.response_generator = response_generator or ResponseGenerator(lead_qualifier=self.lead_qualifier)

    def handle(self, message: str, state: ConversationState) -> ConversationResult:
        state.response_variant += 1
        intent = self.intent_detector.detect(message)
        updated_state = self.lead_qualifier.update(state, message, intent.intent)
        response = self.response_generator.generate(intent.intent, message, updated_state)
        text = str(message or "").strip().lower()
        word_count = len(text.split())
        tool_like_request = "follow up" in text and "lead" in text
        needs_llm_fallback = intent.intent == ConversationIntent.GENERAL_CONVERSATION or (intent.intent == ConversationIntent.UNKNOWN and word_count > 3)
        return ConversationResult(
            response=response,
            intent=intent.intent,
            confidence=intent.confidence,
            should_respond_directly=not (tool_like_request or needs_llm_fallback),
            stage=updated_state.stage,
            metadata={
                "intent_reason": intent.reason,
                "previous_intent": updated_state.previous_intent.value if updated_state.previous_intent else None,
                "lead": {
                    "interest": updated_state.lead.interest,
                    "business_type": updated_state.lead.business_type,
                    "industry": updated_state.lead.industry,
                    "team_size": updated_state.lead.team_size,
                    "budget": updated_state.lead.budget,
                    "timeline": updated_state.lead.timeline,
                    "monthly_volume": updated_state.lead.monthly_volume,
                },
                "lead_stage": updated_state.lead_stage.value,
                "preferred_language": updated_state.preferred_language,
            },
        )
