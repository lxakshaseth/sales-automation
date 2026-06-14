import asyncio

from app.intelligence.confidence import calculate_confidence, calculate_tool_confidence
from app.intelligence.confidence.models import ConfidenceLevel
from app.intelligence.confidence.scoring_service import confidence_bucket, weighted_score


def test_weighted_score_uses_layer_three_weights():
    score = weighted_score(
        {
            "retrieval_confidence": 0.95,
            "tool_confidence": 1.00,
            "intent_confidence": 0.80,
            "response_confidence": 0.90,
        }
    )

    assert score == 0.935


def test_confidence_engine_returns_high_confidence_result():
    result = asyncio.run(
        calculate_confidence(
            {
                "retrieval_score": 0.95,
                "rerank_score": 0.92,
                "chunk_relevance": 0.91,
                "chunk_scores": [0.95, 0.91, 0.88],
                "chunk_count": 3,
                "tool_output": {"success": True, "tool_name": "crm_lookup", "result": {"lead_id": "123"}},
                "tool_exists": True,
                "parameters_validated": True,
                "intent_confidence": 0.80,
                "llm_response": {"answer": "Lead found and verified."},
                "structured_output_valid": True,
                "schema_validation_success": True,
            }
        )
    )

    assert result.confidence_level == ConfidenceLevel.HIGH
    assert result.recommendation == {}
    assert result.indicators["retrieval_supported"] is True
    assert result.indicators["tool_verified"] is True
    assert result.indicators["schema_valid"] is True
    assert result.indicators["hallucination_risk"] is False
    assert "tool_verified" in result.reason
    assert "high_retrieval_match" in result.reason
    assert "valid_intent" in result.reason


def test_confidence_engine_requests_clarification_for_low_confidence():
    result = asyncio.run(
        calculate_confidence(
            {
                "retrieval_score": 0.55,
                "rerank_score": 0.50,
                "chunk_relevance": 0.52,
                "chunk_scores": [0.55, 0.50],
                "chunk_count": 2,
                "tool_output": {"tool_name": "lead_lookup"},
                "tool_exists": True,
                "parameters_validated": True,
                "intent_confidence": 0.50,
                "llm_response": {"answer": "Lead may need follow-up."},
                "structured_output_valid": False,
                "schema_validation_success": True,
            }
        )
    )

    assert result.confidence_level == ConfidenceLevel.LOW
    assert result.recommendation == {"action": "request_clarification"}
    assert result.fallback_required is True


def test_confidence_engine_returns_fallback_for_very_low_confidence():
    result = asyncio.run(
        calculate_confidence(
            {
                "retrieval_score": 0.10,
                "rerank_score": 0.10,
                "chunk_relevance": 0.10,
                "chunk_scores": [],
                "chunk_count": 0,
                "tool_output": {"success": False, "tool_name": "calendar_booking", "error": "invalid date"},
                "tool_exists": True,
                "parameters_validated": False,
                "intent_confidence": 0.10,
                "llm_response": "I am not sure.",
                "structured_output_valid": False,
                "schema_validation_success": False,
                "unsupported_claims": ["unsupported booking confirmation"],
            }
        )
    )

    assert result.confidence_level == ConfidenceLevel.VERY_LOW
    assert result.recommendation == {"action": "fallback_response"}
    assert result.indicators["hallucination_risk"] is True


def test_tool_failure_confidence_is_zero():
    result = asyncio.run(
        calculate_tool_confidence(
            tool_output={"success": False, "tool_name": "email_sender", "error": "smtp timeout"},
            tool_exists=True,
            parameters_validated=True,
        )
    )

    assert result.confidence == 0.0
    assert result.tool_verified is False


def test_confidence_buckets_match_required_thresholds():
    assert confidence_bucket(0.80) == ConfidenceLevel.HIGH
    assert confidence_bucket(0.60) == ConfidenceLevel.MEDIUM
    assert confidence_bucket(0.40) == ConfidenceLevel.LOW
    assert confidence_bucket(0.39) == ConfidenceLevel.VERY_LOW
