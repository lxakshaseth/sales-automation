import asyncio

from app.intelligence.hallucination import HallucinationGuard, RiskLevel, SourceVerifier, ValidationAction


def test_guard_allows_grounded_high_confidence_response():
    async def run():
        return await HallucinationGuard().validate_response(
            {
                "response": "The lead prefers email follow-up.",
                "retrieved_chunks": [{"content": "The lead prefers email follow-up.", "score": 0.92}],
                "confidence": 0.91,
            }
        )

    result = asyncio.run(run())

    assert result.valid is True
    assert result.action == ValidationAction.ALLOW
    assert result.report.risk.risk_level == RiskLevel.LOW_RISK
    assert result.fallback is None


def test_guard_rejects_email_success_without_tool_success():
    async def run():
        return await HallucinationGuard().validate_response(
            {
                "response": "Email sent successfully.",
                "retrieved_chunks": [{"content": "The lead asked for an email follow-up.", "score": 0.90}],
                "tool_outputs": [{"tool_name": "email_sender", "success": False, "error": "smtp timeout"}],
                "confidence": 0.90,
            }
        )

    result = asyncio.run(run())

    assert result.valid is False
    assert result.action == ValidationAction.REJECT
    assert result.fallback is not None
    assert result.fallback.response == "I could not verify this information."
    assert "email_success_claim_without_tool_success" in result.report.grounding.tool_failures


def test_guard_allows_email_success_with_verified_tool_output():
    async def run():
        return await HallucinationGuard().validate_response(
            {
                "response": "Email sent successfully.",
                "tool_outputs": [{"tool_name": "email_sender", "success": True, "result": {"status": "Email sent successfully."}}],
                "system_context": [{"content": "Email sent successfully."}],
                "confidence": 0.95,
            }
        )

    result = asyncio.run(run())

    assert result.valid is True
    assert result.action == ValidationAction.ALLOW
    assert result.report.grounding.tool_grounded is True


def test_guard_requests_clarification_for_low_confidence():
    async def run():
        return await HallucinationGuard().validate_response(
            {
                "response": "The lead prefers WhatsApp follow-up.",
                "retrieved_chunks": [{"content": "The lead prefers WhatsApp follow-up.", "score": 0.88}],
                "confidence": 0.52,
            }
        )

    result = asyncio.run(run())

    assert result.valid is False
    assert result.action == ValidationAction.WARNING
    assert result.fallback is not None
    assert result.fallback.action == ValidationAction.WARNING
    assert result.fallback.response == "I need additional information before I can answer confidently."


def test_guard_rejects_very_low_confidence():
    async def run():
        return await HallucinationGuard().validate_response(
            {
                "response": "The lead prefers WhatsApp follow-up.",
                "retrieved_chunks": [{"content": "The lead prefers WhatsApp follow-up.", "score": 0.88}],
                "confidence": 0.35,
            }
        )

    result = asyncio.run(run())

    assert result.valid is False
    assert result.action == ValidationAction.REJECT
    assert result.fallback is not None
    assert result.report.risk.risk_level in {RiskLevel.HIGH_RISK, RiskLevel.CRITICAL_RISK}


def test_source_verifier_flags_unsupported_claims():
    verifier = SourceVerifier()

    result = verifier.verify_sources(
        "The lead has a confirmed meeting tomorrow.",
        retrieved_chunks=[{"content": "The lead asked for pricing information."}],
    )

    assert result.verified is False
    assert result.coverage == 0.0
    assert result.unsupported_claims == ["The lead has a confirmed meeting tomorrow."]
