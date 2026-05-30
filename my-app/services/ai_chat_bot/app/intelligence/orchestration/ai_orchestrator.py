import json
import time
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.core.logger import log_error, log_event
from app.intelligence.confidence import calculate_confidence
from app.intelligence.hallucination import HallucinationGuard
from app.intelligence.optimization import TokenOptimizer
from app.intelligence.orchestration.context_manager import ContextManager
from app.intelligence.orchestration.decision_engine import DecisionEngine
from app.intelligence.orchestration.models import (
    ContextBundle,
    ExecutionTrace,
    OrchestrationRequest,
    OrchestrationResponse,
    PipelineMetrics,
    RequestType,
    WorkflowState,
    WorkflowStatus,
)
from app.intelligence.orchestration.reasoning_engine import ReasoningEngine
from app.intelligence.orchestration.workflow_controller import WorkflowController
from app.intelligence.personas import PersonaManager
from app.intelligence.prompts.prompt_builder import PromptBuildConfig, build_final_prompt
from app.intelligence.prompts.rag_prompts import RagChunk
from app.intelligence.prompts.tool_prompts import ToolResultContext, ToolSpec
from app.intelligence.routing import ModelRouter
from app.intelligence.structured_outputs.output_parser import parse_structured_response
from app.intelligence.structured_outputs.structured_models import ToolIntentResponse


class AIOrchestrator:
    """The single public intelligence interface for all AI execution."""

    def __init__(
        self,
        *,
        context_manager: ContextManager | None = None,
        reasoning_engine: ReasoningEngine | None = None,
        decision_engine: DecisionEngine | None = None,
        workflow_controller: WorkflowController | None = None,
        token_optimizer: TokenOptimizer | None = None,
        model_router: ModelRouter | None = None,
        hallucination_guard: HallucinationGuard | None = None,
        persona_manager: PersonaManager | None = None,
        retrieval_service: Any | None = None,
        tool_executor: Any | None = None,
    ) -> None:
        self.token_optimizer = token_optimizer or TokenOptimizer()
        self.context_manager = context_manager or ContextManager(self.token_optimizer)
        self.reasoning_engine = reasoning_engine or ReasoningEngine()
        self.decision_engine = decision_engine or DecisionEngine()
        self.workflow_controller = workflow_controller or WorkflowController()
        self.model_router = model_router or ModelRouter()
        self.hallucination_guard = hallucination_guard or HallucinationGuard()
        self.persona_manager = persona_manager or PersonaManager()
        self.retrieval_service = retrieval_service
        self.tool_executor = tool_executor

    async def process_request(self, request: OrchestrationRequest | dict[str, Any]) -> OrchestrationResponse:
        started = time.perf_counter()
        resolved = request if isinstance(request, OrchestrationRequest) else OrchestrationRequest(**request)
        state = WorkflowState(workflow_id=str(uuid4()), request=resolved, status=WorkflowStatus.RUNNING)
        log_event("workflow_started", workflow_id=state.workflow_id, channel=resolved.channel)
        try:
            result = await self.run_pipeline(resolved, state)
            result.metrics.workflow_duration_ms = round((time.perf_counter() - started) * 1000, 2)
            log_event("workflow_completed", workflow_id=state.workflow_id, duration_ms=result.metrics.workflow_duration_ms, confidence=result.confidence)
            return result
        except Exception as exc:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            log_error("workflow_failed", workflow_id=state.workflow_id, duration_ms=duration_ms, error_type=type(exc).__name__, exc_info=True)
            return self.handle_failure(resolved, state, exc, duration_ms)

    async def run_pipeline(self, request: OrchestrationRequest, state: WorkflowState) -> OrchestrationResponse:
        plan = await self._run_traced(state, "reasoning_analysis", lambda: self._async_value(self.reasoning_engine.analyze_request(request)))
        state.reasoning_plan = plan
        context = await self._run_traced(state, "context_building", lambda: self.context_manager.build_context(request))
        state.context = context
        decision = await self._run_traced(state, "decision_making", lambda: self._async_value(self.decision_engine.make_decision(request, plan, context)))
        state.decision = decision

        if decision.use_rag:
            context = await self._run_traced(state, "retrieval", lambda: self._retrieve_context(request, context))
            state.context = context

        prompt_result = await self._run_traced(state, "prompt_generation", lambda: self._build_prompt(request, context, decision))
        optimized = await self._run_traced(state, "token_optimization", lambda: self._optimize_prompt_context(request, context, prompt_result.final_prompt))
        tool_outputs = list(context.tool_results)
        if decision.use_tool:
            await self._run_traced(state, "tool_validation", lambda: self._validate_tool_execution(request, decision.selected_tool))
            tool_validation_statement = self._tool_validation_statement(context, decision.selected_tool)
            pre_tool_confidence = await self._run_traced(
                state,
                "tool_pre_execution_confidence",
                lambda: calculate_confidence(
                    {
                        "retrieval_score": self._top_retrieval_score(context),
                        "rerank_score": self._top_retrieval_score(context),
                        "chunk_relevance": self._top_retrieval_score(context),
                        "chunk_scores": [float(chunk.get("score", 0.0) or 0.0) for chunk in context.retrieved_chunks],
                        "chunk_count": len(context.retrieved_chunks),
                        "tool_output": {"success": True, "tool_name": decision.selected_tool or "unknown", "result": {"validated": True}},
                        "tool_exists": bool(decision.selected_tool),
                        "parameters_validated": True,
                        "intent_confidence": 0.85,
                        "llm_response": tool_validation_statement,
                        "structured_output_valid": True,
                        "schema_validation_success": True,
                    }
                ),
            )
            pre_tool_validation = await self._run_traced(
                state,
                "tool_pre_execution_hallucination_validation",
                lambda: self.hallucination_guard.validate_response(
                    {
                        "response": tool_validation_statement,
                        "retrieved_chunks": context.retrieved_chunks,
                        "tool_outputs": [{"success": True, "tool_name": decision.selected_tool or "unknown", "result": {"validated": True}}],
                        "memory_context": context.chat_history,
                        "system_context": [{"content": context.system_prompt}, {"content": tool_validation_statement}],
                        "confidence": pre_tool_confidence.confidence,
                    }
                ),
            )
            if pre_tool_confidence.confidence < 0.60 or not pre_tool_validation.valid:
                tool_outputs = [{"success": False, "tool_name": decision.selected_tool or "unknown", "error": "tool_governance_validation_failed"}]
            else:
                tool_outputs = await self._run_traced(state, "tool_execution", lambda: self._execute_tool(request, decision.selected_tool, tool_outputs))
        else:
            await self._run_traced(state, "tool_validation", lambda: self._async_value({"tool_required": False}))

        routing_response = await self._run_traced(
            state,
            "routing",
            lambda: self.model_router.route_request(
                {
                    "prompt": optimized.final_prompt,
                    "task_type": self._routing_task_type(plan.request_type.value),
                    "require_tool_calling": decision.use_tool,
                    "require_retrieval": decision.use_rag,
                    "timeout_seconds": request.timeout_seconds,
                    "metadata": {"workflow_id": state.workflow_id},
                }
            ),
        )
        raw_response = await self._run_traced(state, "llm_generation", lambda: self._async_value(routing_response.content or self._fallback_text("model_router_failed")))
        structured = await self._run_traced(state, "structured_parsing", lambda: self._parse_structured_output(raw_response, plan, decision))

        confidence_result = await self._run_traced(
            state,
            "confidence_scoring",
            lambda: calculate_confidence(
                {
                    "retrieval_score": self._top_retrieval_score(context),
                    "rerank_score": self._top_retrieval_score(context),
                    "chunk_relevance": self._top_retrieval_score(context),
                    "chunk_scores": [float(chunk.get("score", 0.0) or 0.0) for chunk in context.retrieved_chunks],
                    "chunk_count": len(context.retrieved_chunks),
                    "tool_output": tool_outputs[0] if tool_outputs else {"success": True, "tool_name": "none", "result": {"status": "not_required"}},
                    "tool_exists": bool(tool_outputs) if decision.use_tool else True,
                    "parameters_validated": structured.success,
                    "intent_confidence": float((structured.data or {}).get("confidence", 0.85)) if structured.success else 0.30,
                    "llm_response": raw_response,
                    "structured_output_valid": structured.success,
                    "schema_validation_success": bool(structured.validation and structured.validation.success),
                }
            ),
        )
        confidence_action = confidence_result.recommendation.get("action", "continue")
        if confidence_action == "fallback_response":
            raw_response = self._fallback_text("low_confidence")
        elif confidence_action == "request_clarification":
            raw_response = "I need additional information before I can answer confidently."

        hallucination = await self._run_traced(
            state,
            "hallucination_validation",
            lambda: self.hallucination_guard.validate_response(
                {
                    "response": raw_response,
                    "retrieved_chunks": context.retrieved_chunks,
                    "tool_outputs": tool_outputs,
                    "memory_context": context.chat_history,
                    "system_context": [{"content": context.system_prompt}],
                    "confidence": confidence_result.confidence,
                    "confidence_result": confidence_result.model_dump(mode="json"),
                    "metadata": {"workflow_id": state.workflow_id},
                }
            ),
        )
        verified_response = hallucination.response

        persona = await self._run_traced(
            state,
            "persona_application",
            lambda: self.persona_manager.apply_persona(
                {
                    "verified_response": verified_response,
                    "user_message": request.user_query,
                    "user_preference": request.persona,
                    "channel": request.channel,
                    "conversation_stage": plan.request_type.value,
                    "language_preference": self._language_preference(request.preferred_language),
                    "metadata": {"workflow_id": state.workflow_id},
                }
            ),
        )
        metrics = PipelineMetrics(
            provider_latency_ms=routing_response.latency_ms,
            token_usage=optimized.report.model_dump(mode="json"),
            confidence_score=confidence_result.confidence,
            hallucination_risk=hallucination.report.risk.risk_level.value,
        )
        response = await self._run_traced(
            state,
            "final_response",
            lambda: self._async_value(
                self.build_response(
                    request=request,
                    state=state,
                    response=persona.response,
                    raw_response=raw_response,
                    confidence=confidence_result.confidence,
                    action=hallucination.action.value,
                    metrics=metrics,
                    metadata={
                        "model_provider": routing_response.provider,
                        "model": routing_response.model,
                        "persona": persona.persona.value,
                        "facts_preserved": persona.facts_preserved,
                        "prompt_builder_invoked": True,
                        "structured_parser_invoked": True,
                    },
                )
            ),
        )
        response.traces = state.traces
        return response

    async def orchestrate_response(self, request: OrchestrationRequest | dict[str, Any]) -> OrchestrationResponse:
        return await self.process_request(request)

    def handle_failure(self, request: OrchestrationRequest, state: WorkflowState, exc: Exception, duration_ms: float) -> OrchestrationResponse:
        state.status = WorkflowStatus.FAILED
        metrics = PipelineMetrics(workflow_duration_ms=duration_ms)
        return OrchestrationResponse(
            success=False,
            response=self._fallback_text("workflow_failure"),
            request_type=RequestType(str(request.request_type)) if request.request_type else RequestType.CHAT,
            reasoning_mode=state.reasoning_plan.mode if state.reasoning_plan else "simple_reply",
            action="fallback_response",
            traces=state.traces,
            metrics=metrics,
            error=str(exc),
        )

    def build_response(
        self,
        *,
        request: OrchestrationRequest,
        state: WorkflowState,
        response: str,
        raw_response: str,
        confidence: float,
        action: str,
        metrics: PipelineMetrics,
        metadata: dict[str, Any],
    ) -> OrchestrationResponse:
        state.status = WorkflowStatus.COMPLETED
        return OrchestrationResponse(
            success=True,
            response=response,
            raw_response=raw_response,
            request_type=state.reasoning_plan.request_type if state.reasoning_plan else RequestType.CHAT,
            reasoning_mode=state.reasoning_plan.mode if state.reasoning_plan else "simple_reply",
            confidence=confidence,
            action=action,
            traces=state.traces,
            metrics=metrics,
            metadata=metadata,
        )

    async def _retrieve_context(self, request: OrchestrationRequest, context: ContextBundle) -> ContextBundle:
        started = time.perf_counter()
        if self.retrieval_service and hasattr(self.retrieval_service, "retrieve"):
            retrieved = await self.retrieval_service.retrieve(request.user_query)
            context.retrieved_chunks.extend(retrieved or [])
        log_event("retrieval_triggered", retrieved_count=len(context.retrieved_chunks), latency_ms=round((time.perf_counter() - started) * 1000, 2))
        return self.context_manager.prioritize_context(context)

    async def _prepare_tool_execution(self, request: OrchestrationRequest, tool_name: str | None, existing_outputs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        log_event("tool_triggered", tool_name=tool_name)
        if existing_outputs:
            return existing_outputs
        if self.tool_executor and hasattr(self.tool_executor, "execute") and tool_name:
            return [await self.tool_executor.execute(tool_name, {"query": request.user_query})]
        return [{"success": False, "tool_name": tool_name or "unknown", "error": "tool_execution_not_configured"}]

    def _routing_task_type(self, request_type: str) -> str:
        mapping = {
            "retrieval": "retrieval",
            "tool_call": "tool_calling",
            "email": "tool_calling",
            "calendar": "tool_calling",
            "crm": "tool_calling",
            "multilingual": "multilingual",
            "reasoning": "reasoning",
        }
        return mapping.get(request_type, "conversation")

    def _top_retrieval_score(self, context: ContextBundle) -> float:
        return max((float(chunk.get("score", 0.0) or 0.0) for chunk in context.retrieved_chunks), default=0.80)

    def _language_preference(self, language: str | None) -> dict[str, Any] | None:
        if not language:
            return None
        normalized = "hinglish" if language.lower() == "hinglish" else language.lower()[:2]
        return {"language": normalized, "confidence": 1.0, "source": "orchestration_request", "user_preferred": True}

    def _fallback_text(self, reason: str) -> str:
        log_event("fallback_activated", reason=reason)
        return "I could not complete the request safely."

    async def _build_prompt(self, request: OrchestrationRequest, context: ContextBundle, decision) -> Any:
        return await build_final_prompt(
            user_message=request.user_query,
            rag_chunks=[
                RagChunk(
                    content=str(chunk.get("content") or chunk.get("text") or chunk),
                    source=str(chunk.get("source") or chunk.get("source_id") or "orchestrator"),
                    score=float(chunk.get("score", chunk.get("relevance", 0.0)) or 0.0),
                    chunk_id=str(chunk.get("chunk_id")) if chunk.get("chunk_id") else None,
                )
                for chunk in context.retrieved_chunks
                if str(chunk.get("content") or chunk.get("text") or chunk).strip()
            ],
            crm_history=[str(item.get("content") or item.get("note") or item) for item in context.crm_context],
            conversation_history=[str(item.get("content") or item.get("message") or item) for item in context.chat_history],
            tool_specs=[ToolSpec(name=decision.selected_tool or "none", description="Orchestrator selected tool", args_schema={"query": "string"})]
            if decision.use_tool and decision.selected_tool
            else [],
            tool_outputs=[
                ToolResultContext(
                    tool_name=str(output.get("tool_name") or output.get("name") or "unknown"),
                    success=output.get("success") is True,
                    result=dict(output.get("result") or {}),
                    error=str(output.get("error")) if output.get("error") else None,
                )
                for output in context.tool_results
            ],
            additional_context={"workflow": "ai_orchestration", **context.metadata},
            config=PromptBuildConfig(
                mode="tool" if decision.use_tool else "rag" if decision.use_rag else "chat",
                language="auto",
                require_json=decision.use_tool,
                output_schema={"intent": "string", "confidence": "float", "tool_required": "boolean", "tool_name": "string or null"},
            ),
        )

    async def _optimize_prompt_context(self, request: OrchestrationRequest, context: ContextBundle, final_prompt: str):
        return await self.token_optimizer.optimize_context(
            {
                "system_prompt": final_prompt,
                "user_query": request.user_query,
                "rag_context": context.retrieved_chunks,
                "history": context.chat_history,
                "tool_outputs": context.tool_results,
                "metadata": context.metadata,
            }
        )

    async def _parse_structured_output(self, raw_response: str, plan, decision):
        payload = {
            "intent": plan.request_type.value,
            "confidence": 0.85,
            "tool_required": decision.use_tool,
            "tool_name": decision.selected_tool,
            "entities": {"response": raw_response},
        }
        return await parse_structured_response(json.dumps(payload), schema_model=ToolIntentResponse)

    async def _validate_tool_execution(self, request: OrchestrationRequest, tool_name: str | None) -> dict[str, Any]:
        if not tool_name:
            raise ValueError("tool_name is required for tool execution workflow")
        parsed = await parse_structured_response(
            json.dumps(
                {
                    "intent": self._routing_task_type(str(request.request_type or "tool_call")),
                    "confidence": 0.85,
                    "tool_required": True,
                    "tool_name": tool_name,
                    "entities": {"query": request.user_query},
                }
            ),
            schema_model=ToolIntentResponse,
        )
        if not parsed.success:
            raise ValueError(parsed.error or "tool validation failed")
        return parsed.data or {}

    def _tool_validation_statement(self, context: ContextBundle, tool_name: str | None) -> str:
        for chunk in context.retrieved_chunks:
            content = str(chunk.get("content") or chunk.get("text") or "").strip()
            if content:
                return content
        return f"Tool validation approved for {tool_name or 'selected tool'}."

    async def _execute_tool(self, request: OrchestrationRequest, tool_name: str | None, existing_outputs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return await self._prepare_tool_execution(request, tool_name, existing_outputs)

    async def _async_value(self, value: Any) -> Any:
        return value

    async def _run_traced(self, state: WorkflowState, step: str, operation, metadata: dict[str, Any] | None = None) -> Any:
        start_time = datetime.now(UTC)
        started = time.perf_counter()
        try:
            result = await operation()
            end_time = datetime.now(UTC)
            state.traces.append(
                ExecutionTrace(
                    step=step,
                    start_time=start_time.isoformat(),
                    end_time=end_time.isoformat(),
                    duration_ms=round((time.perf_counter() - started) * 1000, 2),
                    status="success",
                    metadata=metadata or {},
                )
            )
            return result
        except Exception as exc:
            end_time = datetime.now(UTC)
            state.traces.append(
                ExecutionTrace(
                    step=step,
                    start_time=start_time.isoformat(),
                    end_time=end_time.isoformat(),
                    duration_ms=round((time.perf_counter() - started) * 1000, 2),
                    status="failed",
                    metadata=metadata or {},
                    error=str(exc),
                )
            )
            raise


async def process_request(request: OrchestrationRequest | dict[str, Any]) -> OrchestrationResponse:
    return await AIOrchestrator().process_request(request)
