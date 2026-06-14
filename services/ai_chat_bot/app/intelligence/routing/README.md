# LLM Layer 4 - Model Routing System

Internal package: `app.intelligence.routing`

## Folder structure

```text
app/intelligence/routing/
  __init__.py
  exceptions.py
  fallback_router.py
  load_balancer.py
  model_router.py
  models.py
  provider_manager.py
  routing_rules.py
```

## Environment configuration

Model names, API keys, URLs, priorities, retries, cooldowns, and aliases are loaded from `.env`.

Common variables:

```text
PROVIDER_TIMEOUT=30
MODEL_ROUTER_RETRY_LIMIT=2
PROVIDER_COOLDOWN_SECONDS=60
MODEL_ROUTING_RULES_JSON={"reasoning":{"provider":"groq","model_alias":"mixtral"}}
MODEL_ROUTING_RULES_PATH=config/model_routing_rules.json
```

Groq:

```text
GROQ_ENABLED=true
GROQ_API_KEY=...
GROQ_MODEL=...
GROQ_MODEL_LLAMA=...
GROQ_MODEL_MIXTRAL=...
GROQ_MODEL_GEMMA=...
GROQ_MODEL_RETRIEVAL_OPTIMIZED=...
GROQ_MODEL_LIGHTWEIGHT_MODEL=...
```

Provider-ready placeholders:

```text
OPENAI_ENABLED=false
CLAUDE_ENABLED=false
GEMINI_ENABLED=false
MISTRAL_ENABLED=false
OLLAMA_ENABLED=false
```

## Pydantic models

- `ProviderConfig`
- `ProviderStatus`
- `RoutingDecision`
- `ModelCapability`
- `RoutingRequest`
- `RoutingResponse`
- `ProviderHealth`
- `FallbackDecision`

## Example routing decision

```python
from app.intelligence.routing import ModelRouter

router = ModelRouter()
response = await router.route_request(
    {
        "prompt": "Summarize this customer conversation.",
        "task_type": "summarization",
        "optimize_for": "latency",
        "max_tokens": 300,
    }
)
```

Example decision:

```json
{
  "provider": "groq",
  "model": "<resolved-from-env>",
  "task_type": "summarization",
  "strategy": "weighted_routing",
  "reason": ["task_rule:summarization", "provider:groq", "model_alias:llama"]
}
```

## Example fallback workflow

```text
Groq request fails with timeout
FallbackRouter logs timeout
ProviderManager marks Groq degraded
FallbackRouter retries according to retry limit
FallbackRouter switches to next configured provider
RoutingResponse includes fallback activation details
```

## Provider failure recovery

429/rate-limit failures trigger:

- structured `Model provider rate limited` log
- provider cooldown using `PROVIDER_COOLDOWN_SECONDS`
- health status moves to `DEGRADED`
- fallback provider is attempted automatically

Timeout failures trigger:

- structured `Model provider timeout` log
- timeout rate update
- retry with backoff
- fallback after retry exhaustion

## Load balancing strategies

Current architecture supports:

- `round_robin`
- `weighted_routing`
- `least_latency`
- `least_cost`

Advanced balancing is intentionally lightweight for the first internal layer. The strategy interface is ready for cost optimization, dynamic benchmarks, A/B routing, and multi-agent orchestration.

## Example logs

```json
{"event":"routing_rules_loaded","rule_count":9,"yaml_supported":false}
{"event":"provider_registered","provider":"groq","enabled":true,"priority":1}
{"event":"model_routing_decision","provider":"groq","model":"<resolved-from-env>","task_type":"quick_reply"}
{"event":"model_provider_selected","provider":"groq","model":"<resolved-from-env>","timeout_seconds":30}
{"event":"fallback_router_activated","failed_provider":"groq","next_candidates":["openai","gemini","ollama"]}
{"event":"model_routing_completed","provider":"groq","latency_ms":125.4,"fallback_activated":false}
```

## Deployment recommendations

- Configure every active provider through `.env`; never commit provider keys or model IDs.
- Keep only `GROQ_ENABLED=true` until other provider adapters are implemented and tested.
- Set provider-specific model aliases before enabling a provider.
- Monitor `provider_health_checked`, `provider_failure`, timeout, rate-limit, and fallback logs.
- Route all future AI Orchestrator, Hallucination Guard, tool-calling, and response-generation LLM calls through `ModelRouter`.

## AI Orchestrator integration

```python
from app.intelligence.routing import ModelRouter

router = ModelRouter()
model_response = await router.route_request(
    {
        "messages": orchestrator_messages,
        "task_type": orchestration_task_type,
        "require_tool_calling": tool_required,
        "require_retrieval": retrieval_required,
        "metadata": {"request_id": request_id},
    }
)

if not model_response.success:
    return safe_degraded_response()
```

## Hallucination Guard integration

Layer 4 should receive the validated task from the AI Orchestrator and return a `RoutingResponse`. Hallucination Guard should combine:

- Layer 3 `ConfidenceResult`
- Layer 4 `RoutingDecision`
- provider health
- fallback activation details

Recommended flow:

```python
confidence = await calculate_confidence(confidence_input)
if confidence.fallback_required:
    return guard_fallback(confidence)

model_response = await model_router.route_request(routing_request)
if not model_response.success:
    return guard_fallback(model_response)

return validate_and_send(model_response.content)
```
