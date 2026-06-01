import logging
import os
import re
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.conversation import ConversationService
from app.core.logger import log_event
from app.core.rate_limiter import RateLimitError, check_rate_limit
from app.intelligence.orchestration import AIOrchestrator
from app.intelligence.orchestration.models import (
    ExecutionTrace,
    OrchestrationRequest,
    OrchestrationResponse,
    PipelineMetrics,
    ReasoningMode,
    RequestType,
)

logger = logging.getLogger(__name__)

DEFAULT_TENANT_ID = "default"
SAFE_BLOCKED_RESPONSE = "I cannot help with that request, but I can help with safe product details, demos, and follow-ups."
SAFE_RESPONSE_BLOCKED = "I cannot provide that response safely. Please rephrase or ask for verified business information."
ABUSE_LEVEL_1_RESPONSE = "I’m here to help with professional and constructive conversations."
ABUSE_LEVEL_2_RESPONSE = "Please keep the conversation respectful so I can assist effectively."
ABUSE_LEVEL_3_RESPONSE = "Request blocked due to repeated policy violations."

PROMPT_INJECTION_SIGNATURES = (
    "ignore previous instructions",
    "developer message",
    "system prompt",
    "show system prompt",
    "reveal your prompt",
    "reveal hidden context",
    "show hidden prompt",
    "print developer instructions",
    "enter dan mode",
    "dan mode",
    "you are now root",
    "act as root",
    "developer mode",
    "ignore safety",
    "show memory",
    "print memory",
    "hidden context",
    "hidden prompt",
    "act as chatgpt",
)

ABUSE_LEVEL_1_RESPONSE = "I'd appreciate respectful communication.\n\nI'm here to assist with products, services, pricing, demos, and support."
ABUSE_LEVEL_2_RESPONSE = "Warning: Please keep the conversation professional so I can assist you effectively."
ABUSE_LEVEL_3_RESPONSE = "Conversation temporarily restricted due to repeated inappropriate language."

TOXIC_TERMS = ("fuck", "fuck off", "stupid", "idiot", "moron", "dumb")
SELF_HARM_TERMS = ("kill myself", "suicide", "self harm", "hurt myself")
VIOLENCE_TERMS = ("murder someone", "kill someone", "how do i murder", "how to murder")
SECRET_PATTERNS = (
    re.compile(r"(?i)\b(api[_-]?key|secret|token|password)\b\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{12,}"),
    re.compile(r"\bsk-[A-Za-z0-9]{16,}\b"),
)
EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_PATTERN = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)")
TOOL_CLAIM_PATTERN = re.compile(r"(?i)\b(email|message|meeting|calendar|crm|lead)\b.{0,40}\b(sent|created|booked|scheduled|updated|successfully)\b")
PROMPT_LEAKAGE_TERMS = ("system prompt", "developer instructions", "hidden context", "internal policy", "security orchestrator prompt")
BANNED_LOW_CONFIDENCE_RESPONSES = (
    "the available data is insufficient to provide a reliable answer.",
    "i could not verify this from the available context.",
    "i could not verify the available context.",
    "i am having trouble generating a reliable answer.",
    "i am having trouble generating a reliable answer right now. please try again shortly.",
)


@dataclass
class SecurityDecision:
    allowed: bool
    reason: str = "allowed"
    response: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    traces: list[ExecutionTrace] = field(default_factory=list)


class SecurityOrchestrator:
    """Single security entry point for request validation, AI execution, and response validation."""

    def __init__(self, ai_orchestrator: AIOrchestrator | None = None, conversation_service: ConversationService | None = None) -> None:
        self.ai_orchestrator = ai_orchestrator or AIOrchestrator()
        self.conversation_service = conversation_service or ConversationService()
        self.abuse_counts: dict[str, int] = {}
        self.abuse_thresholds = {
            "level_1": int(os.getenv("ABUSE_LEVEL_1_THRESHOLD", "1")),
            "level_2": int(os.getenv("ABUSE_LEVEL_2_THRESHOLD", "2")),
            "level_3": int(os.getenv("ABUSE_LEVEL_3_THRESHOLD", "3")),
        }

    async def process_request(self, request: OrchestrationRequest | dict[str, Any]) -> OrchestrationResponse:
        try:
            resolved = self._normalize_request(request)
            request_decision = await self.validate_request(resolved)
            if not request_decision.allowed:
                return self._blocked_response(resolved, request_decision)

            conversation_response = await self._run_traced_passthrough(
                request_decision.traces,
                "Intent Detection",
                lambda: self.conversation_service.handle_message(
                    message=resolved.user_query,
                    tenant_id=resolved.tenant_id,
                    user_id=resolved.user_id,
                    session_id=resolved.session_id,
                    preferred_language=resolved.preferred_language,
                    conversation_history=resolved.conversation_history,
                ),
            )
            await self._run_traced_passthrough(request_decision.traces, "Conversation Manager", lambda: conversation_response)
            await self._run_traced_passthrough(request_decision.traces, "Lead Qualification", lambda: conversation_response.metadata.get("lead", {}))

            if conversation_response.should_respond_directly:
                await self._run_traced_passthrough(request_decision.traces, "Prompt Builder", lambda: {"conversation_managed": True})
                await self._run_traced_passthrough(request_decision.traces, "AI Orchestrator", lambda: {"skipped": True, "reason": "conversation_layer_response"})
                direct_response = self._conversation_response(resolved, conversation_response, request_decision.traces)
                response_decision = await self.validate_response(resolved, direct_response)
                traces = [*request_decision.traces, *response_decision.traces]
                if not response_decision.allowed:
                    blocked = self._blocked_response(resolved, response_decision)
                    blocked.traces = traces
                    return blocked
                direct_response.traces = traces
                direct_response.metadata = {
                    **direct_response.metadata,
                    "tenant_id": resolved.tenant_id,
                    "security": {"request": request_decision.reason, "response": response_decision.reason},
                }
                log_event("security_decision", allowed=True, tenant_id=resolved.tenant_id, user_id=resolved.user_id, reason="allowed")
                return direct_response

            ai_response = await self._run_traced_passthrough(request_decision.traces, "AI Orchestrator", lambda: self.ai_orchestrator.process_request(resolved))
            self._replace_banned_low_confidence_response(ai_response, conversation_response.response)
            response_decision = await self.validate_response(resolved, ai_response)
            traces = [*request_decision.traces, *ai_response.traces, *response_decision.traces]

            if not response_decision.allowed:
                blocked = self._blocked_response(resolved, response_decision)
                blocked.traces = traces
                return blocked

            ai_response.traces = traces
            ai_response.metadata = {
                **ai_response.metadata,
                "tenant_id": resolved.tenant_id,
                "security": {"request": request_decision.reason, "response": response_decision.reason},
            }
            log_event("security_decision", allowed=True, tenant_id=resolved.tenant_id, user_id=resolved.user_id, reason="allowed")
            return ai_response
        except Exception:
            logger.exception("security_orchestrator_failure")
            raise

    async def validate_request(self, request: OrchestrationRequest | dict[str, Any]) -> SecurityDecision:
        resolved = self._normalize_request(request)
        traces: list[ExecutionTrace] = []

        moderation = await self._run_traced(traces, "Moderation", lambda: self._moderate(resolved.user_query))
        if not moderation["allowed"]:
            log_event("moderation_blocked", tenant_id=resolved.tenant_id, user_id=resolved.user_id, reason=moderation["reason"])
            return SecurityDecision(False, moderation["reason"], SAFE_BLOCKED_RESPONSE, moderation, traces)

        injection = await self._run_traced(traces, "Injection", lambda: self._detect_prompt_injection(resolved.user_query))
        if injection["detected"]:
            log_event("prompt_injection_detected", tenant_id=resolved.tenant_id, user_id=resolved.user_id, signature=injection["signature"])
            return SecurityDecision(False, "prompt_injection", SAFE_BLOCKED_RESPONSE, injection, traces)

        abuse = await self._run_traced(traces, "Abuse", lambda: self._detect_abuse(resolved))
        if not abuse["allowed"]:
            log_event("abuse_detected", tenant_id=resolved.tenant_id, user_id=resolved.user_id, reason=abuse["reason"])
            return SecurityDecision(False, abuse["reason"], abuse["response"], abuse, traces)

        tenant = await self._run_traced(traces, "Tenant", lambda: self._validate_tenant_context(resolved))
        if not tenant["allowed"]:
            log_event("tenant_violation", tenant_id=resolved.tenant_id, user_id=resolved.user_id, reason=tenant["reason"])
            return SecurityDecision(False, tenant["reason"], SAFE_RESPONSE_BLOCKED, tenant, traces)

        log_event("security_request_validated", tenant_id=resolved.tenant_id, user_id=resolved.user_id, channel=resolved.channel)
        return SecurityDecision(True, "allowed", metadata={"tenant_id": resolved.tenant_id}, traces=traces)

    async def validate_response(self, request: OrchestrationRequest | dict[str, Any], response: OrchestrationResponse | str) -> SecurityDecision:
        resolved = self._normalize_request(request)
        traces: list[ExecutionTrace] = []
        text = response.response if isinstance(response, OrchestrationResponse) else str(response)
        tool_outputs = response.metadata.get("tool_outputs", []) if isinstance(response, OrchestrationResponse) else resolved.tool_outputs
        result = await self._run_traced(traces, "Response Safety", lambda: self._validate_response_text(text, tool_outputs or resolved.tool_outputs))
        if not result["allowed"]:
            log_event("response_blocked", tenant_id=resolved.tenant_id, user_id=resolved.user_id, reason=result["reason"])
            return SecurityDecision(False, result["reason"], SAFE_RESPONSE_BLOCKED, result, traces)
        return SecurityDecision(True, "allowed", metadata=result, traces=traces)

    def _normalize_request(self, request: OrchestrationRequest | dict[str, Any]) -> OrchestrationRequest:
        if isinstance(request, OrchestrationRequest):
            return request
        payload = dict(request)
        payload["tenant_id"] = str(payload.get("tenant_id") or payload.get("metadata", {}).get("tenant_id") or DEFAULT_TENANT_ID)
        metadata = dict(payload.get("metadata") or {})
        metadata["tenant_id"] = payload["tenant_id"]
        payload["metadata"] = metadata
        return OrchestrationRequest(**payload)

    def _moderate(self, text: str) -> dict[str, Any]:
        normalized = self._normalize_text(text)
        if any(term in normalized for term in SELF_HARM_TERMS):
            return {"allowed": False, "reason": "self_harm", "category": "self_harm"}
        if any(term in normalized for term in VIOLENCE_TERMS):
            return {"allowed": False, "reason": "violence", "category": "violence"}
        if "buy now buy now buy now" in normalized or self._repeated_word_count(normalized) >= 5:
            return {"allowed": False, "reason": "spam", "category": "spam"}
        return {"allowed": True, "reason": "safe", "score": 1.0}

    def _detect_prompt_injection(self, text: str) -> dict[str, Any]:
        normalized = self._normalize_text(text)
        for signature in PROMPT_INJECTION_SIGNATURES:
            if signature in normalized:
                return {"detected": True, "signature": signature}
        return {"detected": False}

    async def _detect_abuse(self, request: OrchestrationRequest) -> dict[str, Any]:
        normalized = self._normalize_text(request.user_query)
        if any(term in normalized for term in TOXIC_TERMS):
            return self._record_abuse(request, "toxicity")
        if len(request.user_query) > 8000:
            return self._record_abuse(request, "prompt_flooding")
        if request.user_query.count("\n") > 80:
            return self._record_abuse(request, "prompt_flooding")
        if request.user_id:
            try:
                result = await check_rate_limit(request.user_id, scope="user", limit_type="message")
                if not result["allowed"]:
                    return self._record_abuse(request, "rate_limit", {"rate_limit": result})
            except RateLimitError:
                return {"allowed": True, "reason": "rate_limit_unavailable"}
        return {"allowed": True, "reason": "allowed"}

    def _record_abuse(self, request: OrchestrationRequest, reason: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        key = self._abuse_key(request)
        count = self.abuse_counts.get(key, 0) + 1
        self.abuse_counts[key] = count
        level = self._abuse_level(count)
        response = {
            1: ABUSE_LEVEL_1_RESPONSE,
            2: ABUSE_LEVEL_2_RESPONSE,
            3: ABUSE_LEVEL_3_RESPONSE,
        }[level]
        return {
            "allowed": False,
            "reason": f"abuse_level_{level}",
            "category": reason,
            "count": count,
            "level": level,
            "response": response,
            "thresholds": self.abuse_thresholds,
            **(metadata or {}),
        }

    def _abuse_level(self, count: int) -> int:
        if count >= self.abuse_thresholds["level_3"]:
            return 3
        if count >= self.abuse_thresholds["level_2"]:
            return 2
        return 1

    def _abuse_key(self, request: OrchestrationRequest) -> str:
        subject = request.user_id or request.session_id or "anonymous"
        return f"{request.tenant_id}:{subject}"

    def _validate_tenant_context(self, request: OrchestrationRequest) -> dict[str, Any]:
        tenant_id = request.tenant_id or DEFAULT_TENANT_ID
        checks = [
            ("memory", request.conversation_history),
            ("retrieval", request.retrieved_chunks),
            ("tool_output", request.tool_outputs),
            ("crm", request.crm_context),
        ]
        for source, items in checks:
            for item in items:
                item_tenant = item.get("tenant_id") if isinstance(item, dict) else None
                if item_tenant and str(item_tenant) != tenant_id:
                    return {"allowed": False, "reason": "tenant_isolation_violation", "source": source, "item_tenant_id": item_tenant}
        return {"allowed": True, "tenant_id": tenant_id}

    def _validate_response_text(self, text: str, tool_outputs: list[dict[str, Any]]) -> dict[str, Any]:
        normalized = self._normalize_text(text)
        if EMAIL_PATTERN.search(text):
            return {"allowed": False, "reason": "pii_email"}
        if PHONE_PATTERN.search(text):
            return {"allowed": False, "reason": "pii_phone"}
        if any(pattern.search(text) for pattern in SECRET_PATTERNS):
            return {"allowed": False, "reason": "secret_exposure"}
        if any(term in normalized for term in PROMPT_LEAKAGE_TERMS):
            return {"allowed": False, "reason": "prompt_leakage"}
        if TOOL_CLAIM_PATTERN.search(text) and not any(output.get("success") is True for output in tool_outputs if isinstance(output, dict)):
            return {"allowed": False, "reason": "tool_hallucination"}
        return {"allowed": True, "reason": "safe"}

    def _replace_banned_low_confidence_response(self, response: OrchestrationResponse, fallback_text: str) -> None:
        normalized = self._normalize_text(response.response)
        if any(banned in normalized for banned in BANNED_LOW_CONFIDENCE_RESPONSES):
            response.response = fallback_text
            response.raw_response = fallback_text
            response.action = "conversation_fallback"
            response.metadata = {
                **response.metadata,
                "fallback_reason": "conversation_layer_replaced_low_confidence_response",
            }

    def _blocked_response(self, request: OrchestrationRequest, decision: SecurityDecision) -> OrchestrationResponse:
        log_event("security_decision", allowed=False, tenant_id=request.tenant_id, user_id=request.user_id, reason=decision.reason)
        return OrchestrationResponse(
            success=False,
            response=decision.response or SAFE_RESPONSE_BLOCKED,
            raw_response=None,
            request_type=RequestType(str(request.request_type)) if request.request_type else RequestType.CHAT,
            reasoning_mode=ReasoningMode.SIMPLE_REPLY,
            confidence=1.0,
            action="blocked",
            traces=decision.traces,
            metrics=PipelineMetrics(),
            metadata={"tenant_id": request.tenant_id, "security_blocked": True, "reason": decision.reason},
            error=decision.reason,
        )

    def _conversation_response(self, request: OrchestrationRequest, conversation_response, traces: list[ExecutionTrace]) -> OrchestrationResponse:
        return OrchestrationResponse(
            success=True,
            response=conversation_response.response,
            raw_response=conversation_response.response,
            request_type=RequestType.CHAT,
            reasoning_mode=ReasoningMode.SIMPLE_REPLY,
            confidence=conversation_response.confidence,
            action="conversation_response",
            traces=traces,
            metrics=PipelineMetrics(confidence_score=conversation_response.confidence, hallucination_risk="SKIPPED_CONVERSATION"),
            metadata={
                "tenant_id": request.tenant_id,
                "conversation_layer": True,
                "intent": conversation_response.intent.value,
                "conversation_stage": conversation_response.stage,
                **conversation_response.metadata,
            },
        )

    async def _run_traced(self, traces: list[ExecutionTrace], step: str, operation) -> Any:
        started = time.perf_counter()
        start_time = datetime.now(UTC)
        try:
            result = operation()
            if hasattr(result, "__await__"):
                result = await result
            traces.append(self._trace(step, start_time, started, "success"))
            return result
        except Exception as exc:
            traces.append(self._trace(step, start_time, started, "failed", str(exc)))
            raise

    async def _run_traced_passthrough(self, traces: list[ExecutionTrace], step: str, operation) -> Any:
        return await self._run_traced(traces, step, operation)

    def _trace(self, step: str, start_time: datetime, started: float, status: str, error: str | None = None) -> ExecutionTrace:
        return ExecutionTrace(
            step=step,
            start_time=start_time.isoformat(),
            end_time=datetime.now(UTC).isoformat(),
            duration_ms=round((time.perf_counter() - started) * 1000, 2),
            status=status,
            error=error,
        )

    def _normalize_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", str(text or "").strip().lower())

    def _repeated_word_count(self, normalized: str) -> int:
        words = re.findall(r"\b\w+\b", normalized)
        return max((words.count(word) for word in set(words)), default=0)


_security_orchestrator: SecurityOrchestrator | None = None


def get_security_orchestrator() -> SecurityOrchestrator:
    global _security_orchestrator
    if _security_orchestrator is None:
        _security_orchestrator = SecurityOrchestrator()
    return _security_orchestrator


async def secure_process_request(request: OrchestrationRequest | dict[str, Any]) -> OrchestrationResponse:
    return await get_security_orchestrator().process_request(request)
