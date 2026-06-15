# LLM Layer 6 - Hallucination Reduction Layer

Internal package: `app.intelligence.hallucination`

## Folder structure

```text
app/intelligence/hallucination/
  __init__.py
  exceptions.py
  fact_checker.py
  hallucination_guard.py
  models.py
  response_grounding.py
  source_verifier.py
  validation_pipeline.py
```

## Pydantic models

- `ValidationResult`
- `HallucinationReport`
- `SourceVerification`
- `GroundingResult`
- `FactCheckResult`
- `RiskAssessment`
- `FallbackResponse`

## Example validation workflow

```python
from app.intelligence.hallucination import HallucinationGuard

result = await HallucinationGuard().validate_response(
    {
        "response": "The lead prefers email follow-up.",
        "retrieved_chunks": [{"content": "Lead prefers email follow-up.", "score": 0.92}],
        "tool_outputs": [],
        "memory_context": [],
        "confidence": 0.91,
    }
)
```

## Tool verification

The guard rejects success claims unless tool output confirms success:

```json
{
  "tool_name": "email_sender",
  "success": true
}
```

Without this, claims such as `Email sent successfully`, `Meeting booked successfully`, and `Lead created` are blocked.

## Source verification

The source verifier compares response claims against:

- retrieved chunks
- verified tool outputs
- conversation memory
- CRM records
- system-generated context

If evidence is missing, unsupported claims are returned and the response is rejected or downgraded.

## Example hallucination report

```json
{
  "valid": false,
  "action": "fallback_response",
  "risk": {
    "risk_level": "HIGH_RISK",
    "risk_score": 0.75,
    "factors": ["unsupported_claims", "tool_verification_failure"]
  }
}
```

## Safe fallbacks

```json
{"response": "I could not verify this information."}
{"response": "The available data is insufficient to provide a reliable answer."}
{"response": "I need additional information before I can answer confidently."}
```

## Example logs

```json
{"event":"hallucination_check_started","confidence":0.92}
{"event":"source_verification_completed","verified":true,"coverage":1.0}
{"event":"response_grounding_completed","grounded":true,"violation_count":0}
{"event":"fact_check_completed","passed":true,"unsupported_claim_count":0}
{"event":"hallucination_validation_result","valid":true,"action":"allow","risk_level":"LOW_RISK"}
```

## Persona System Layer 7 integration

Persona System should generate style and tone only. It must not bypass Layer 6 or introduce new factual claims after validation.

Recommended future order:

```text
Model response
Persona style constraints
Hallucination Guard
Final user response
```

If Persona Layer 7 modifies facts after Layer 6, the modified response must be sent through `HallucinationGuard.validate_response()` again.
