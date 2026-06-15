# LLM Layer 5 - Token Optimization Layer

Internal package: `app.intelligence.optimization`

## Folder structure

```text
app/intelligence/optimization/
  __init__.py
  cache_optimizer.py
  context_compressor.py
  exceptions.py
  memory_summarizer.py
  models.py
  prompt_optimizer.py
  token_optimizer.py
```

## Environment budgets

```text
MAX_CONTEXT_TOKENS=12000
MAX_RAG_TOKENS=4000
MAX_HISTORY_TOKENS=3000
MAX_TOOL_OUTPUT_TOKENS=1000
MAX_SYSTEM_PROMPT_TOKENS=1000
RESERVED_RESPONSE_TOKENS=1000
TOKEN_OPTIMIZER_MODEL=llama-3.3-70b-versatile
```

## Pydantic models

- `TokenBudget`
- `TokenUsage`
- `OptimizationReport`
- `CompressionResult`
- `MemorySummary`
- `ContextMetrics`
- `TokenAllocation`

## Example optimization workflow

```python
from app.intelligence.optimization import TokenOptimizer

optimizer = TokenOptimizer()
optimized = await optimizer.optimize_context(
    {
        "system_prompt": "You are a helpful sales assistant.",
        "user_query": "Follow up with this lead.",
        "rag_context": [{"content": "Lead prefers email.", "score": 0.95}],
        "history": [{"role": "user", "content": "Budget is 10k."}],
        "tool_outputs": [{"success": True, "lead_id": "123", "raw": "..."}],
    }
)
```

## Example context compression

Two chunks with 95% similarity are deduplicated. RAG chunks below score `0.50` are removed. The retained chunks are sorted by score and trimmed to `MAX_RAG_TOKENS`.

## Example history summarization

The memory summarizer preserves:

- user goals
- decisions made
- CRM notes
- active tasks

It removes greetings, repeated messages, completed chatter, and low-value acknowledgements.

## Example token report

```json
{
  "original_tokens": 14500,
  "optimized_tokens": 7800,
  "saved_tokens": 6700,
  "compression_ratio": 46.21,
  "overflow_prevented": true
}
```

## Overflow handling

When limits are exceeded:

1. Compress duplicate and low-value context.
2. Summarize conversation history.
3. Trim lower-priority sections first.
4. Fall back to the current user query if optimization fails.

The optimizer never intentionally returns a prompt above the configured input budget.

## Example logs

```json
{"event":"token_optimization_started","max_context_tokens":12000}
{"event":"context_duplicates_removed","duplicate_count":2}
{"event":"rag_low_value_chunks_removed","dropped_chunks":1}
{"event":"history_summarized","original_messages":50,"summarized_messages":8}
{"event":"token_optimization_completed","original_tokens":14500,"optimized_tokens":7800,"saved_tokens":6700,"compression_ratio":46.21}
```

## Persona System integration

Persona prompts should be passed as `system_prompt`. The optimizer preserves system prompt priority first, trims it only against `MAX_SYSTEM_PROMPT_TOKENS`, and keeps the current user query above all lower-priority context.

## AI Orchestrator integration

```python
from app.intelligence.optimization import TokenOptimizer
from app.intelligence.routing import ModelRouter

optimized = await TokenOptimizer().optimize_context(raw_context)

response = await ModelRouter().route_request(
    {
        "prompt": optimized.final_prompt,
        "task_type": raw_context.get("task_type"),
        "metadata": {
            "token_report": optimized.report.model_dump(),
        },
    }
)
```

Layer 5 should be the single source of truth for context size management before every `ModelRouter` call.
