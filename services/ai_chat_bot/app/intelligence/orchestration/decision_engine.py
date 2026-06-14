from app.core.logger import log_event
from app.intelligence.orchestration.exceptions import DecisionError
from app.intelligence.orchestration.models import ContextBundle, DecisionResult, OrchestrationRequest, ReasoningMode, ReasoningPlan


class DecisionEngine:
    """Makes routing, retrieval, tool, confidence, and fallback decisions."""

    def should_use_rag(self, plan: ReasoningPlan, context: ContextBundle) -> bool:
        return plan.use_retrieval or bool(context.retrieved_chunks)

    def should_use_tool(self, plan: ReasoningPlan) -> bool:
        return plan.use_tool and bool(plan.tool_name)

    def should_route_model(self, request: OrchestrationRequest) -> bool:
        return bool(request.user_query.strip())

    def should_trigger_fallback(self, confidence: float | None = None, error: str | None = None) -> bool:
        return bool(error) or (confidence is not None and confidence < 0.40)

    def make_decision(self, request: OrchestrationRequest, plan: ReasoningPlan, context: ContextBundle) -> DecisionResult:
        try:
            decision = DecisionResult(
                use_rag=self.should_use_rag(plan, context),
                use_tool=self.should_use_tool(plan),
                route_model=self.should_route_model(request),
                selected_tool=plan.tool_name if self.should_use_tool(plan) else None,
                reasons=[f"mode:{plan.mode.value}", f"type:{plan.request_type.value}"],
            )
            if plan.mode == ReasoningMode.TOOL_EXECUTION:
                decision.reasons.append("tool_validation_required")
            log_event("orchestration_decision_made", use_rag=decision.use_rag, use_tool=decision.use_tool, selected_tool=decision.selected_tool)
            return decision
        except Exception as exc:
            raise DecisionError("failed to make orchestration decision") from exc
