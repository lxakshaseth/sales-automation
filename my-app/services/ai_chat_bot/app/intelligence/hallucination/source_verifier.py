import re
from difflib import SequenceMatcher
from typing import Any

from app.core.logger import log_error, log_event
from app.intelligence.hallucination.models import SourceVerification


class SourceVerifier:
    """Verifies response claims against trusted evidence sources."""

    def verify_sources(
        self,
        response: str,
        *,
        retrieved_chunks: list[dict[str, Any]] | None = None,
        tool_outputs: list[dict[str, Any]] | None = None,
        memory_context: list[dict[str, Any]] | None = None,
        system_context: list[dict[str, Any]] | None = None,
    ) -> SourceVerification:
        try:
            sources = self._collect_sources(retrieved_chunks, tool_outputs, memory_context, system_context)
            claims = self._extract_claims(response)
            matched, unsupported = self.match_response_to_sources(claims, sources)
            coverage = self.calculate_source_coverage(matched, claims)
            result = SourceVerification(
                verified=bool(claims) and coverage >= 0.60 and not unsupported,
                coverage=coverage,
                matched_claims=matched,
                unsupported_claims=unsupported,
                evidence_sources=[source["source_id"] for source in sources],
                missing_sources=[] if sources else ["trusted_sources"],
            )
            log_event(
                "source_verification_completed",
                verified=result.verified,
                coverage=result.coverage,
                unsupported_claim_count=len(result.unsupported_claims),
            )
            return result
        except Exception as exc:
            log_error("Source verification failed", exc_info=True, error_type=type(exc).__name__)
            return SourceVerification(
                verified=False,
                coverage=0.0,
                unsupported_claims=[response],
                missing_sources=["source_verification_failed"],
            )

    def match_response_to_sources(self, claims: list[str], sources: list[dict[str, str]]) -> tuple[list[str], list[str]]:
        matched: list[str] = []
        unsupported: list[str] = []
        for claim in claims:
            if self._is_low_risk_phrase(claim):
                matched.append(claim)
                continue
            best = max((self._similarity(claim, source["content"]) for source in sources), default=0.0)
            keyword_supported = any(self._keyword_overlap(claim, source["content"]) >= 0.55 for source in sources)
            if best >= 0.72 or keyword_supported:
                matched.append(claim)
            else:
                unsupported.append(claim)
        return matched, unsupported

    def calculate_source_coverage(self, matched_claims: list[str], claims: list[str]) -> float:
        if not claims:
            return 0.0
        return round(len(matched_claims) / len(claims), 4)

    def detect_unsupported_claims(self, response: str, sources: list[dict[str, Any]]) -> list[str]:
        claims = self._extract_claims(response)
        _, unsupported = self.match_response_to_sources(claims, self._normalize_sources(sources, "source"))
        if unsupported:
            log_event("unsupported_claims_detected", unsupported_claim_count=len(unsupported))
        return unsupported

    def _collect_sources(
        self,
        retrieved_chunks: list[dict[str, Any]] | None,
        tool_outputs: list[dict[str, Any]] | None,
        memory_context: list[dict[str, Any]] | None,
        system_context: list[dict[str, Any]] | None,
    ) -> list[dict[str, str]]:
        return [
            *self._normalize_sources(retrieved_chunks or [], "retrieval"),
            *self._normalize_sources(tool_outputs or [], "tool"),
            *self._normalize_sources(memory_context or [], "memory"),
            *self._normalize_sources(system_context or [], "system"),
        ]

    def _normalize_sources(self, sources: list[dict[str, Any]], prefix: str) -> list[dict[str, str]]:
        normalized = []
        for index, source in enumerate(sources):
            content = str(source.get("content") or source.get("text") or source.get("result") or source)
            if content.strip():
                normalized.append({"source_id": str(source.get("id") or source.get("source_id") or f"{prefix}:{index}"), "content": content})
        return normalized

    def _extract_claims(self, response: str) -> list[str]:
        raw = re.split(r"(?<=[.!?])\s+|\n+", response)
        claims = [claim.strip(" -\t") for claim in raw if len(claim.strip()) >= 8]
        return claims or [response.strip()]

    def _similarity(self, claim: str, source: str) -> float:
        return SequenceMatcher(None, claim.lower(), source.lower()).ratio()

    def _keyword_overlap(self, claim: str, source: str) -> float:
        claim_words = self._words(claim)
        source_words = self._words(source)
        if not claim_words:
            return 0.0
        return len(claim_words & source_words) / len(claim_words)

    def _words(self, value: str) -> set[str]:
        stop = {"the", "a", "an", "and", "or", "to", "for", "is", "are", "was", "were", "this", "that", "with", "your", "you"}
        return {word for word in re.findall(r"[a-zA-Z0-9_]+", value.lower()) if word not in stop and len(word) > 2}

    def _is_low_risk_phrase(self, claim: str) -> bool:
        value = claim.strip().lower()
        return value in {"i could not verify this information.", "i need additional information before i can answer confidently."}
