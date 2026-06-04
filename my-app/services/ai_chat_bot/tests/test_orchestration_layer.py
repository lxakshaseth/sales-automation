import asyncio

from app.intelligence.confidence.models import ConfidenceLevel, ConfidenceMetrics, ConfidenceResult
from app.intelligence.hallucination.models import (
    FactCheckResult,
    GroundingResult,
    HallucinationReport,
    RiskAssessment,
    RiskLevel,
    SourceVerification,
    ValidationAction,
    ValidationResult,
)
from app.intelligence.hallucination.validation_pipeline import ValidationPipeline
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


class UnavailableModelRouter:
    async def route_request(self, request):
        return RoutingResponse(
            success=False,
            latency_ms=12.0,
            error="All model providers are temporarily unavailable.",
            error_type="FallbackExhaustedError",
        )


class LowConfidenceRetryRouter:
    def __init__(self, retry_success: bool = True):
        self.calls = []
        self.retry_success = retry_success

    async def route_request(self, request):
        self.calls.append(request)
        if len(self.calls) == 1:
            return RoutingResponse(success=True, content="I am not sure.", provider="fake", model="weak-model", latency_ms=8.0)
        if self.retry_success:
            return RoutingResponse(
                success=True,
                content="The lead prefers email follow-up.",
                provider="groq",
                model="llama-3.3-70b-versatile",
                latency_ms=10.0,
            )
        return RoutingResponse(
            success=False,
            provider="groq",
            model="llama-3.3-70b-versatile",
            latency_ms=10.0,
            error="All model providers are temporarily unavailable.",
            error_type="FallbackExhaustedError",
        )


class UnsupportedAnswerRetryRouter:
    def __init__(self, retry_success: bool = True):
        self.calls = []
        self.retry_success = retry_success

    async def route_request(self, request):
        self.calls.append(request)
        if len(self.calls) == 1:
            return RoutingResponse(success=True, content="The available data is insufficient to provide a reliable answer.", provider="fake", model="weak-model", latency_ms=8.0)
        if self.retry_success:
            return RoutingResponse(
                success=True,
                content="We provide sales automation services, including WhatsApp follow-ups, lead tracking, reminders, and reporting.",
                provider="groq",
                model="llama-3.3-70b-versatile",
                latency_ms=10.0,
            )
        return RoutingResponse(
            success=False,
            provider="groq",
            model="llama-3.3-70b-versatile",
            latency_ms=10.0,
            error="All model providers are temporarily unavailable.",
            error_type="FallbackExhaustedError",
        )


class StaticModelRouter:
    def __init__(self, content: str):
        self.content = content
        self.calls = []

    async def route_request(self, request):
        self.calls.append(request)
        return RoutingResponse(success=True, content=self.content, provider="fake", model="fake-model", latency_ms=5.0)


class SequenceHallucinationGuard:
    def __init__(self, valid_sequence):
        self.valid_sequence = list(valid_sequence)

    async def validate_response(self, validation_input):
        valid = self.valid_sequence.pop(0)
        response = validation_input["response"]
        if valid:
            return _hallucination_result(valid=True, response=response, risk=RiskLevel.LOW_RISK, action=ValidationAction.ALLOW)
        return _hallucination_result(
            valid=False,
            response="The available data is insufficient to provide a reliable answer.",
            original_response=response,
            risk=RiskLevel.HIGH_RISK,
            action=ValidationAction.REJECT,
        )


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
        return await orchestrator.process_request({"user_query": "Need pricing details", "channel": "whatsapp"})

    response = asyncio.run(run())

    assert response.success is False
    assert response.action == "fallback_response"
    assert response.response == "I could not complete the request safely."
    assert response.error


def test_orchestrator_reports_provider_unavailable_without_hallucination_fallback():
    async def run():
        orchestrator = AIOrchestrator(model_router=UnavailableModelRouter())
        return await orchestrator.process_request({"user_query": "time", "channel": "default"})

    response = asyncio.run(run())

    assert response.success is True
    assert response.action == "fallback_response"
    assert response.response == (
        "I can still help while the AI provider is unavailable.\n\n"
        "Could you share what you need help with: products, services, pricing, a demo, or support?"
    )
    assert response.raw_response == "All model providers are temporarily unavailable."
    assert response.confidence == 0.0
    assert response.metrics.hallucination_risk == "NOT_EVALUATED"
    assert response.metadata["routing_error_type"] == "FallbackExhaustedError"
    assert "hallucination_validation" not in {trace.step for trace in response.traces}


def test_fallback_only_on_provider_failure():
    async def run():
        orchestrator = AIOrchestrator(model_router=UnavailableModelRouter())
        return await orchestrator.process_request({"user_query": "Can you tell me about your product?", "channel": "whatsapp"})

    response = asyncio.run(run())

    assert response.success is True
    assert response.action == "fallback_response"
    assert response.metadata["routing_error_type"] == "FallbackExhaustedError"


def test_greeting_response():
    async def run():
        orchestrator = AIOrchestrator(model_router=UnavailableModelRouter())
        return await orchestrator.process_request({"user_query": "hi", "channel": "whatsapp"})

    response = asyncio.run(run())

    assert response.success is True
    assert response.action == "respond"
    assert response.response == "Hello! How can I help you today?"
    assert response.metadata["greeting_allowlist"] is True


def test_small_talk_response():
    router = StaticModelRouter("I'm doing well and ready to help with your sales automation questions.")

    async def run():
        orchestrator = AIOrchestrator(model_router=router)
        return await orchestrator.process_request({"user_query": "how are you", "channel": "whatsapp"})

    response = asyncio.run(run())

    assert response.success is True
    assert response.action == "allow"
    assert response.response == "I'm doing well and ready to help with your sales automation questions."
    assert response.metrics.hallucination_risk == "LOW_RISK"
    assert len(router.calls) == 1


def test_sales_query_response():
    router = StaticModelRouter("We provide sales automation services for WhatsApp follow-ups, lead tracking, reminders, and reporting.")

    async def run():
        orchestrator = AIOrchestrator(model_router=router)
        return await orchestrator.process_request({"user_query": "I need service", "channel": "whatsapp"})

    response = asyncio.run(run())

    assert response.success is True
    assert response.action == "allow"
    assert "sales automation services" in response.response
    assert response.response != "The available data is insufficient to provide a reliable answer."


def test_hallucination_gate_for_factual_claims():
    async def run():
        return await ValidationPipeline().run_validation_pipeline(
            {
                "response": "I booked the meeting and updated the CRM.",
                "retrieved_chunks": [],
                "tool_outputs": [],
                "memory_context": [],
                "system_context": [],
                "confidence": 0.9,
                "metadata": {"request_type": "chat", "reasoning_mode": "simple_reply"},
            }
        )

    report = asyncio.run(run())

    assert report.valid is False
    assert report.action == ValidationAction.REJECT
    assert "unsupported_claims" in report.risk.factors


def _confidence(confidence: float, *, fallback_required: bool, action: str = "continue") -> ConfidenceResult:
    return ConfidenceResult(
        confidence=confidence,
        confidence_level=ConfidenceLevel.LOW if fallback_required else ConfidenceLevel.HIGH,
        recommendation={} if action == "continue" else {"action": action},
        metrics=ConfidenceMetrics(),
        fallback_required=fallback_required,
    )


def _hallucination_result(
    *,
    valid: bool,
    response: str,
    original_response: str | None = None,
    risk: RiskLevel,
    action: ValidationAction,
) -> ValidationResult:
    report = HallucinationReport(
        valid=valid,
        risk=RiskAssessment(risk_level=risk, risk_score=0.1 if valid else 0.8),
        source_verification=SourceVerification(verified=valid, coverage=1.0 if valid else 0.0),
        grounding=GroundingResult(grounded=valid),
        fact_check=FactCheckResult(passed=valid),
        confidence=0.9 if valid else 0.7,
        action=action,
    )
    return ValidationResult(valid=valid, action=action, response=response, original_response=original_response or response, report=report)


def test_low_confidence_uses_groq(monkeypatch):
    router = LowConfidenceRetryRouter(retry_success=True)
    confidence_results = [
        _confidence(0.35, fallback_required=True, action="fallback_response"),
        _confidence(0.90, fallback_required=False),
    ]

    async def fake_confidence(_payload):
        return confidence_results.pop(0)

    monkeypatch.setattr("app.intelligence.orchestration.ai_orchestrator.calculate_confidence", fake_confidence)

    async def run():
        orchestrator = AIOrchestrator(model_router=router)
        return await orchestrator.process_request(
            {
                "user_query": "What does the lead prefer?",
                "channel": "default",
                "request_type": "retrieval",
                "retrieved_chunks": [{"content": "The lead prefers email follow-up.", "score": 0.95}],
            }
        )

    response = asyncio.run(run())

    assert response.success is True
    assert response.action == "retry_via_groq"
    assert response.response == "The lead prefers email follow-up."
    assert len(router.calls) == 2
    assert router.calls[1]["preferred_provider"] == "groq"
    assert "low_confidence_groq_retry" in {trace.step for trace in response.traces}


def test_groq_failure_returns_professional_fallback(monkeypatch):
    router = LowConfidenceRetryRouter(retry_success=False)

    async def fake_confidence(_payload):
        return _confidence(0.35, fallback_required=True, action="fallback_response")

    monkeypatch.setattr("app.intelligence.orchestration.ai_orchestrator.calculate_confidence", fake_confidence)

    async def run():
        orchestrator = AIOrchestrator(model_router=router)
        return await orchestrator.process_request({"user_query": "What does the lead prefer?", "channel": "default"})

    response = asyncio.run(run())

    assert response.success is True
    assert response.action == "fallback_response"
    assert response.response == (
        "Could you tell me a little more about what you need?\n\n"
        "For example, are you looking for products, services, pricing, a demo, or support?"
    )
    assert response.metadata["fallback_reason"] == "groq_retry_failed"
    assert len(router.calls) == 2


def test_unsupported_answer_uses_groq(monkeypatch):
    router = UnsupportedAnswerRetryRouter(retry_success=True)

    async def fake_confidence(_payload):
        return _confidence(0.90, fallback_required=False)

    monkeypatch.setattr("app.intelligence.orchestration.ai_orchestrator.calculate_confidence", fake_confidence)

    async def run():
        orchestrator = AIOrchestrator(
            model_router=router,
            hallucination_guard=SequenceHallucinationGuard([False, True]),
        )
        return await orchestrator.process_request({"user_query": "Can you provide service?", "channel": "whatsapp"})

    response = asyncio.run(run())

    assert response.success is True
    assert response.action == "retry_via_groq"
    assert "sales automation services" in response.response
    assert response.metadata["retry_reason"] == "unsupported_answer"
    assert len(router.calls) == 2
    assert router.calls[1]["preferred_provider"] == "groq"
    assert "unsupported_answer_groq_retry" in {trace.step for trace in response.traces}


def test_unsupported_answer_groq_failure_returns_professional_fallback(monkeypatch):
    router = UnsupportedAnswerRetryRouter(retry_success=False)

    async def fake_confidence(_payload):
        return _confidence(0.90, fallback_required=False)

    monkeypatch.setattr("app.intelligence.orchestration.ai_orchestrator.calculate_confidence", fake_confidence)

    async def run():
        orchestrator = AIOrchestrator(
            model_router=router,
            hallucination_guard=SequenceHallucinationGuard([False]),
        )
        return await orchestrator.process_request({"user_query": "Can you provide service?", "channel": "whatsapp"})

    response = asyncio.run(run())

    assert response.success is True
    assert response.action == "fallback_response"
    assert response.response == (
        "Could you tell me a little more about what you need?\n\n"
        "For example, are you looking for products, services, pricing, a demo, or support?"
    )
    assert response.metadata["fallback_reason"] == "groq_retry_failed_after_hallucination"
    assert response.response != "The available data is insufficient to provide a reliable answer."
    assert len(router.calls) == 2
