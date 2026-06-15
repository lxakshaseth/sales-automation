from app.conversation.models import ConversationState


class ConversationContextBuilder:
    """Build compact context snapshots for prompts, traces, and tests."""

    def build(self, state: ConversationState) -> dict[str, object]:
        return {
            "tenant_id": state.tenant_id,
            "user_id": state.user_id,
            "previous_intent": state.previous_intent.value if state.previous_intent else None,
            "stage": state.stage,
            "lead_stage": state.lead_stage.value,
            "preferred_language": state.preferred_language,
            "lead": {
                "name": state.lead.name,
                "company": state.lead.company,
                "business_type": state.lead.business_type,
                "industry": state.lead.industry,
                "team_size": state.lead.team_size,
                "interest": state.lead.interest,
                "monthly_volume": state.lead.monthly_volume,
                "budget": state.lead.budget,
                "timeline": state.lead.timeline,
            },
        }
