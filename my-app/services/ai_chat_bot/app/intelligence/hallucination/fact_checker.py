import re
from typing import Any

from app.core.logger import log_event
from app.intelligence.hallucination.models import FactCheckResult
from app.intelligence.hallucination.source_verifier import SourceVerifier


class FactChecker:
    """Detects fabricated or unsupported factual claims."""

    HALLUCINATION_MARKERS = (
        "i have sent",
        "i booked",
        "confirmed booking",
        "created the lead",
        "updated the crm",
        "according to the database",
        "the record shows",
    )

    def __init__(self, source_verifier: SourceVerifier | None = None) -> None:
        self.source_verifier = source_verifier or SourceVerifier()

    def check_facts(self, response: str, evidence: list[dict[str, Any]]) -> FactCheckResult:
        claims = self._extract_claims(response)
        verified: list[str] = []
        unsupported: list[str] = []
        for claim in claims:
            if self.verify_claim(claim, evidence):
                verified.append(claim)
            else:
                unsupported.append(claim)
        indicators = self.detect_hallucination(response, unsupported_claims=unsupported)
        consistency = self.evaluate_fact_consistency(verified, claims)
        result = FactCheckResult(
            passed=not unsupported and not indicators,
            factual_consistency=consistency,
            verified_claims=verified,
            unsupported_claims=unsupported,
            hallucination_indicators=indicators,
        )
        log_event("fact_check_completed", passed=result.passed, unsupported_claim_count=len(unsupported), indicator_count=len(indicators))
        return result

    def verify_claim(self, claim: str, evidence: list[dict[str, Any]]) -> bool:
        unsupported = self.source_verifier.detect_unsupported_claims(claim, evidence)
        return not unsupported

    def detect_hallucination(self, response: str, *, unsupported_claims: list[str] | None = None) -> list[str]:
        lower = response.lower()
        indicators = [marker for marker in self.HALLUCINATION_MARKERS if marker in lower]
        if unsupported_claims:
            indicators.append("unsupported_factual_claims")
        return indicators

    def evaluate_fact_consistency(self, verified_claims: list[str], all_claims: list[str]) -> float:
        if not all_claims:
            return 0.0
        return round(len(verified_claims) / len(all_claims), 4)

    def _extract_claims(self, response: str) -> list[str]:
        claims = [claim.strip() for claim in re.split(r"(?<=[.!?])\s+|\n+", response) if len(claim.strip()) >= 8]
        return claims or [response.strip()]
