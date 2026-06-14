# LLM Layer 8 - Evaluation Framework

Internal package: `app.intelligence.evaluation`

## Folder structure

```text
app/intelligence/evaluation/
  __init__.py
  benchmark_suite.py
  eval_runner.py
  exceptions.py
  hallucination_tests.py
  models.py
  prompt_tests.py
  regression_tests.py
  retrieval_tests.py
  tool_call_tests.py
```

## Example benchmark dataset

```json
{
  "cases": [
    {
      "question": "Send a follow-up email",
      "expected_tool": "email_sender",
      "actual_tool": "email_sender",
      "tool_success": true,
      "expected_answer": "follow-up email",
      "actual_answer": "The follow-up email was sent."
    }
  ]
}
```

CSV datasets are also supported. YAML is intentionally reserved as a placeholder for future support.

## Example evaluation workflow

```python
from app.intelligence.evaluation import BenchmarkSuite, EvalRunner

suite = BenchmarkSuite()
suite.register_benchmark("prompt_smoke", "prompt", cases)
report = await EvalRunner(suite).run_all_evaluations()
```

## Deployment gates

- `APPROVED`: overall score >= 90
- `WARNING`: overall score >= 75
- `REJECTED`: overall score < 75 or blocking regression/failing benchmark

## Example report

```json
{
  "overall_score": 91.4,
  "deployment_decision": {
    "deployment_status": "APPROVED",
    "approved": true
  }
}
```

## Regression workflow

```python
from app.intelligence.evaluation import RegressionEvaluator

result = RegressionEvaluator().run_regression_tests(
    {"overall_score": 94.0},
    {"overall_score": 91.0},
    threshold=5.0
)
```

## Example logs

```json
{"event":"evaluation_run_started","benchmark_count":4}
{"event":"benchmark_result","benchmark":"rag_smoke","score":92.0,"status":"PASS"}
{"event":"regression_passed","baseline_score":94.0,"current_score":91.4}
{"event":"evaluation_run_completed","overall_score":91.4,"deployment_status":"APPROVED"}
```

## AI Orchestrator Layer 9 integration

Layer 9 should call this framework before promoting any prompt, model, routing rule, or AI configuration:

```text
candidate config
evaluation framework
deployment decision
AI orchestrator rollout or block
```

No AI configuration should be deployed unless `deployment_decision.approved` is true.
