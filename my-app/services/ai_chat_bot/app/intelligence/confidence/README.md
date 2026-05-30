# LLM Layer 3 - Confidence Scoring System

Internal package: `app.intelligence.confidence`

## Folder structure

```text
app/intelligence/confidence/
  __init__.py
  confidence_engine.py
  exceptions.py
  models.py
  response_confidence.py
  retrieval_confidence.py
  scoring_service.py
  tool_confidence.py
```

## Models

- `ConfidenceResult`
- `RetrievalConfidence`
- `ToolConfidence`
- `ResponseConfidence`
- `ConfidenceReason`
- `ConfidenceMetrics`
- `ConfidenceLevel`

## Example confidence calculation

```python
from app.intelligence.confidence import calculate_confidence

result = await calculate_confidence(
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
```

Weighted scoring:

```text
retrieval_confidence = 40%
tool_confidence = 30%
intent_confidence = 15%
response_confidence = 15%
```

## Example high confidence response

```json
{
  "confidence": 0.93,
  "confidence_level": "HIGH",
  "reason": ["tool_verified", "high_retrieval_match", "schema_valid", "valid_intent"],
  "recommendation": {},
  "indicators": {
    "retrieval_supported": true,
    "tool_verified": true,
    "schema_valid": true,
    "hallucination_risk": false
  }
}
```

## Example low confidence response

```json
{
  "confidence": 0.52,
  "confidence_level": "LOW",
  "reason": ["low_retrieval_match", "tool_execution_failed", "weak_intent"],
  "recommendation": {
    "action": "request_clarification"
  },
  "indicators": {
    "retrieval_supported": false,
    "tool_verified": false,
    "schema_valid": true,
    "hallucination_risk": false
  }
}
```

If confidence is below `0.40`, the recommendation becomes:

```json
{
  "action": "fallback_response"
}
```

## Tool confidence workflow

```python
from app.intelligence.confidence import calculate_tool_confidence

tool_confidence = await calculate_tool_confidence(
    tool_output={"success": True, "tool_name": "calendar_booking", "result": {"event_id": "evt_1"}},
    tool_exists=True,
    parameters_validated=True,
)
```

Tool success returns `1.0` when the tool exists, parameters are validated, execution succeeds, returned status is successful, and the response is complete. Explicit `{"success": false}` returns `0.0`.

## Retrieval confidence workflow

```python
from app.intelligence.confidence import calculate_retrieval_confidence

retrieval_confidence = await calculate_retrieval_confidence(
    retrieval_score=0.90,
    rerank_score=0.87,
    chunk_relevance=0.84,
    chunk_scores=[0.90, 0.84, 0.79],
    chunk_count=3,
    retrieval_threshold=0.65,
)
```

Similarity above `0.85` contributes a high confidence reason. Similarity below `0.50` contributes a low confidence reason.

## Example logs

```json
{"event":"confidence_calculation_started","event_type":"event"}
{"event":"retrieval_confidence_calculated","confidence":0.925,"confidence_level":"HIGH","chunk_count":3}
{"event":"tool_confidence_calculated","confidence":1.0,"confidence_level":"HIGH","tool_verified":true}
{"event":"response_confidence_calculated","confidence":1.0,"confidence_level":"HIGH","hallucination_risk":false}
{"event":"final_confidence_score","confidence":0.93,"confidence_level":"HIGH","fallback_required":false}
```

## Hallucination Guard integration guide

Layer 4 should consume only `ConfidenceResult` from this package. Treat it as the single source of truth for confidence decisions.

Recommended guard behavior:

```python
confidence = await calculate_confidence(confidence_input)

if confidence.recommendation.get("action") == "fallback_response":
    return fallback_response()

if confidence.recommendation.get("action") == "request_clarification":
    return request_clarification()

if confidence.indicators["hallucination_risk"] is True:
    return safe_response_with_citations()

return execute_or_respond()
```

The guard should inspect:

- `confidence`
- `confidence_level`
- `recommendation.action`
- `indicators.retrieval_supported`
- `indicators.tool_verified`
- `indicators.schema_valid`
- `indicators.hallucination_risk`
