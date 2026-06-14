from typing import Any

from app.core.logger import log_event
from app.intelligence.hallucination.models import GroundingResult


class ResponseGrounder:
    """Ensures generated responses remain grounded in trusted context."""

    EMAIL_SUCCESS_MARKERS = ("email sent", "sent successfully", "email delivered", "delivered successfully")
    MEETING_SUCCESS_MARKERS = ("meeting booked", "appointment booked", "calendar event created", "meeting scheduled")
    CRM_SUCCESS_MARKERS = ("lead created", "crm record created", "lead saved", "contact created")

    def ground_response(
        self,
        response: str,
        *,
        retrieved_chunks: list[dict[str, Any]] | None = None,
        tool_outputs: list[dict[str, Any]] | None = None,
        memory_context: list[dict[str, Any]] | None = None,
    ) -> GroundingResult:
        retrieval_grounded = self.verify_retrieval_grounding(response, retrieved_chunks or [])
        tool_grounding = self.verify_tool_grounding(response, tool_outputs or [])
        memory_grounded = self.verify_memory_grounding(response, memory_context or [])
        violations = []
        if not retrieval_grounded and retrieved_chunks:
            violations.append("retrieval_grounding_missing")
        if tool_grounding["failures"]:
            violations.extend(tool_grounding["failures"])
        grounded = (retrieval_grounded or memory_grounded or bool(tool_outputs)) and not violations
        result = GroundingResult(
            grounded=grounded,
            retrieval_grounded=retrieval_grounded,
            tool_grounded=tool_grounding["grounded"],
            memory_grounded=memory_grounded,
            tool_failures=tool_grounding["failures"],
            violations=violations,
        )
        log_event("response_grounding_completed", grounded=result.grounded, violation_count=len(result.violations))
        return result

    def verify_retrieval_grounding(self, response: str, retrieved_chunks: list[dict[str, Any]]) -> bool:
        if not retrieved_chunks:
            return False
        response_words = self._words(response)
        source_words = set()
        for chunk in retrieved_chunks:
            source_words |= self._words(str(chunk.get("content") or chunk.get("text") or chunk))
        return bool(response_words) and len(response_words & source_words) / len(response_words) >= 0.35

    def verify_tool_grounding(self, response: str, tool_outputs: list[dict[str, Any]]) -> dict[str, Any]:
        lower = response.lower()
        failures: list[str] = []
        if any(marker in lower for marker in self.EMAIL_SUCCESS_MARKERS) and not self._has_successful_tool(tool_outputs, ("email", "smtp", "resend")):
            failures.append("email_success_claim_without_tool_success")
        if any(marker in lower for marker in self.MEETING_SUCCESS_MARKERS) and not self._has_successful_tool(tool_outputs, ("calendar", "meeting", "appointment")):
            failures.append("meeting_success_claim_without_calendar_success")
        if any(marker in lower for marker in self.CRM_SUCCESS_MARKERS) and not self._has_successful_tool(tool_outputs, ("crm", "lead", "hubspot")):
            failures.append("crm_success_claim_without_tool_success")
        return {"grounded": not failures, "failures": failures}

    def verify_memory_grounding(self, response: str, memory_context: list[dict[str, Any]]) -> bool:
        if not memory_context:
            return False
        response_words = self._words(response)
        memory_words = set()
        for memory in memory_context:
            memory_words |= self._words(str(memory.get("content") or memory.get("summary") or memory))
        return bool(response_words) and len(response_words & memory_words) / len(response_words) >= 0.30

    def _has_successful_tool(self, tool_outputs: list[dict[str, Any]], tool_markers: tuple[str, ...]) -> bool:
        for output in tool_outputs:
            haystack = f"{output.get('tool_name', '')} {output.get('name', '')} {output.get('type', '')}".lower()
            if any(marker in haystack for marker in tool_markers) and output.get("success") is True:
                return True
        return False

    def _words(self, value: str) -> set[str]:
        stop = {"the", "a", "an", "and", "or", "to", "for", "is", "are", "was", "were", "this", "that", "with", "your", "you"}
        return {word for word in value.lower().replace(".", " ").replace(",", " ").split() if word not in stop and len(word) > 2}
