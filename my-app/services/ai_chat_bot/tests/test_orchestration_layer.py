import asyncio

from app.intelligence.orchestration import AIOrchestrator, DecisionEngine, ReasoningEngine
from app.intelligence.orchestration.models import ContextBundle, OrchestrationRequest, ReasoningMode, RequestType
from app.intelligence.routing.models import RoutingResponse


class FakeModelRouter:
    async def route_request(self, request):
        prompt = str(request.get("prompt", ""))
        content = "The meeting request is ready for calendar confirmation." if "meeting" in prompt.lower() else "The lead prefers email follow-up."
        return RoutingResponse(success=True, content=content, provider="fake", model="fake-model", latency_ms=12.0)


class FailingModelRouter:
    async def route_request(self, request):
        raise RuntimeError("provider unavailable")


class FakeRetrievalService:
    async def retrieve(self, query):
        return [{"content": "The lead prefers email follow-up.", "score": 0.95}]


class RecordingToolExecutor:
    def __init__(self):
        self.calls = []

    async def execute(self, tool_name, params):
        self.calls.append((tool_name, params))
        return {"success": True, "tool_name": tool_name, "result": {"event_id": "evt_123", "status": "confirmed"}}


def test_reasoning_engine_classifies_email_tool_execution():
    plan = ReasoningEngine().analyze_request(OrchestrationRequest(user_query="Send an email to this lead"))

    assert plan.request_type == RequestType.EMAIL
    assert plan.mode == ReasoningMode.TOOL_EXECUTION
    assert plan.use_tool is True
    assert plan.tool_name == "email_sender"


def test_decision_engine_enables_rag_for_retrieval_plan():
    request = OrchestrationRequest(user_query="Retrieve the lead context", request_type="retrieval")
    plan = ReasoningEngine().analyze_request(request)
    context = ContextBundle(system_prompt="system", current_query=request.user_query)

    decision = DecisionEngine().make_decision(request, plan, context)

    assert decision.use_rag is True
    assert decision.route_model is True


def test_orchestrator_happy_path_with_injected_router():
    async def run():
        orchestrator = AIOrchestrator(model_router=FakeModelRouter(), retrieval_service=FakeRetrievalService())
        return await orchestrator.process_request(
            {
                "user_query": "What does the lead prefer?",
                "request_type": "retrieval",
                "channel": "email",
                "retrieved_chunks": [{"content": "The lead prefers email follow-up.", "score": 0.92}],
            }
        )

    response = asyncio.run(run())

    assert response.success is True
    assert response.response
    assert response.confidence >= 0.80
    assert response.request_type == RequestType.RETRIEVAL
    assert response.reasoning_mode == ReasoningMode.RETRIEVAL
    assert response.metadata["model_provider"] == "fake"
    assert response.metadata["prompt_builder_invoked"] is True
    assert response.metadata["structured_parser_invoked"] is True

    trace_steps = [trace.step for trace in response.traces]
    assert len(trace_steps) > 0
    assert {
        "context_building",
        "prompt_generation",
        "token_optimization",
        "retrieval",
        "routing",
        "llm_generation",
        "structured_parsing",
        "confidence_scoring",
        "hallucination_validation",
        "persona_application",
        "tool_validation",
        "final_response",
    }.issubset(set(trace_steps))
    for trace in response.traces:
        assert trace.start_time
        assert trace.end_time
        assert trace.duration_ms >= 0
        assert trace.status == "success"


def test_orchestrator_enforces_tool_governance_before_execution():
    executor = RecordingToolExecutor()

    async def run():
        orchestrator = AIOrchestrator(
            model_router=FakeModelRouter(),
            tool_executor=executor,
        )
        return await orchestrator.process_request(
            {
                "user_query": "Book a meeting tomorrow at 5 PM",
                "request_type": "calendar",
                "channel": "whatsapp",
                "retrieved_chunks": [{"content": "The meeting request is ready for calendar confirmation.", "score": 0.94}],
            }
        )

    response = asyncio.run(run())
    trace_steps = [trace.step for trace in response.traces]

    assert response.success is True
    assert executor.calls == [("calendar_booking", {"query": "Book a meeting tomorrow at 5 PM"})]
    assert {
        "tool_validation",
        "tool_pre_execution_confidence",
        "tool_pre_execution_hallucination_validation",
        "tool_execution",
    }.issubset(set(trace_steps))
    assert trace_steps.index("tool_validation") < trace_steps.index("tool_pre_execution_confidence")
    assert trace_steps.index("tool_pre_execution_confidence") < trace_steps.index("tool_pre_execution_hallucination_validation")
    assert trace_steps.index("tool_pre_execution_hallucination_validation") < trace_steps.index("tool_execution")


def test_orchestrator_returns_safe_fallback_on_failure():
    async def run():
        orchestrator = AIOrchestrator(model_router=FailingModelRouter())
        return await orchestrator.process_request({"user_query": "Hello", "channel": "whatsapp"})

    response = asyncio.run(run())

    assert response.success is False
    assert response.action == "fallback_response"
    assert response.response == "I could not complete the request safely."
    assert response.error
