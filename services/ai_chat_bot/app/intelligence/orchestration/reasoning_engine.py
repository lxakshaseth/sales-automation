from app.core.logger import log_event
from app.intelligence.orchestration.models import OrchestrationRequest, ReasoningMode, ReasoningPlan, RequestType


class ReasoningEngine:
    """Classifies requests and determines reasoning strategy."""

    def analyze_request(self, request: OrchestrationRequest) -> ReasoningPlan:
        request_type = RequestType(str(request.request_type)) if request.request_type else self._classify(request.user_query)
        mode = self.determine_reasoning_mode(request_type, request.user_query)
        plan = self.build_reasoning_plan(request_type, mode, request.user_query)
        log_event("reasoning_plan_created", request_type=plan.request_type.value, mode=plan.mode.value, use_tool=plan.use_tool, use_retrieval=plan.use_retrieval)
        return plan

    def determine_reasoning_mode(self, request_type: RequestType, query: str) -> ReasoningMode:
        if request_type in {RequestType.EMAIL, RequestType.CALENDAR, RequestType.CRM, RequestType.TOOL_CALL, RequestType.AUTOMATION}:
            return ReasoningMode.TOOL_EXECUTION
        if request_type == RequestType.RETRIEVAL:
            return ReasoningMode.RETRIEVAL
        if request_type == RequestType.REASONING or any(term in query.lower() for term in ("why", "analyze", "compare", "plan")):
            return ReasoningMode.REASONING
        if "then" in query.lower() and "after" in query.lower():
            return ReasoningMode.MULTISTEP_REASONING
        return ReasoningMode.SIMPLE_REPLY

    def build_reasoning_plan(self, request_type: RequestType, mode: ReasoningMode, query: str) -> ReasoningPlan:
        use_tool = mode == ReasoningMode.TOOL_EXECUTION
        use_retrieval = mode in {ReasoningMode.RETRIEVAL, ReasoningMode.REASONING, ReasoningMode.MULTISTEP_REASONING}
        tool_name = self._tool_for(request_type)
        depth = "high" if mode == ReasoningMode.MULTISTEP_REASONING else "medium" if mode in {ReasoningMode.REASONING, ReasoningMode.RETRIEVAL} else "low"
        steps = ["build_context", "optimize_tokens", "route_model", "score_confidence", "validate_hallucination", "apply_persona"]
        if use_retrieval:
            steps.insert(2, "retrieve_context")
        if use_tool:
            steps.append("prepare_tool_execution")
        return ReasoningPlan(request_type=request_type, mode=mode, reasoning_depth=depth, use_retrieval=use_retrieval, use_tool=use_tool, tool_name=tool_name, steps=steps)

    def _classify(self, query: str) -> RequestType:
        lower = query.lower()
        if any(term in lower for term in ("email", "send mail", "follow-up mail")):
            return RequestType.EMAIL
        if any(term in lower for term in ("meeting", "calendar", "appointment", "schedule")):
            return RequestType.CALENDAR
        if any(term in lower for term in ("crm", "lead", "hubspot", "contact")):
            return RequestType.CRM
        if any(term in lower for term in ("retrieve", "document", "knowledge base", "context")):
            return RequestType.RETRIEVAL
        if any(term in lower for term in ("hindi", "hinglish", "translate", "language")):
            return RequestType.MULTILINGUAL
        if any(term in lower for term in ("why", "analyze", "reason")):
            return RequestType.REASONING
        if any(term in lower for term in ("automate", "workflow", "trigger")):
            return RequestType.AUTOMATION
        return RequestType.CHAT

    def _tool_for(self, request_type: RequestType) -> str | None:
        return {
            RequestType.EMAIL: "email_sender",
            RequestType.CALENDAR: "calendar_booking",
            RequestType.CRM: "crm_tool",
            RequestType.TOOL_CALL: "tool_router",
            RequestType.AUTOMATION: "workflow_engine",
        }.get(request_type)
