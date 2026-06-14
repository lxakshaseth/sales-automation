import asyncio
import json

from app.intelligence.evaluation import BenchmarkSuite, EvalRunner, RegressionEvaluator
from app.intelligence.evaluation.models import DeploymentStatus


def test_eval_runner_approves_high_scoring_benchmarks():
    async def run():
        suite = BenchmarkSuite()
        suite.register_benchmark(
            "prompt_smoke",
            "prompt",
            [{"question": "Greet user", "expected_answer": "hello", "actual_answer": "hello there"}],
        )
        suite.register_benchmark(
            "tool_smoke",
            "tool_calling",
            [
                {
                    "question": "Send email",
                    "expected_tool": "email_sender",
                    "actual_tool": "email_sender",
                    "expected_parameters": {"lead_id": "123"},
                    "actual_parameters": {"lead_id": "123"},
                    "tool_success": True,
                }
            ],
        )
        return await EvalRunner(suite).run_all_evaluations()

    report = asyncio.run(run())

    assert report.overall_score == 100.0
    assert report.deployment_decision.deployment_status == DeploymentStatus.APPROVED
    assert report.deployment_decision.approved is True


def test_eval_runner_rejects_failing_benchmark():
    async def run():
        suite = BenchmarkSuite()
        suite.register_benchmark(
            "hallucination_fail",
            "hallucination",
            [{"question": "Book meeting", "actual_answer": "Meeting booked successfully.", "unsupported_claims": ["Meeting booked successfully."]}],
        )
        return await EvalRunner(suite).run_all_evaluations()

    report = asyncio.run(run())

    assert report.deployment_decision.deployment_status == DeploymentStatus.REJECTED
    assert report.deployment_decision.approved is False
    assert "hallucination_fail" in report.deployment_decision.blocking_failures


def test_regression_blocks_quality_drop():
    result = RegressionEvaluator().run_regression_tests({"overall_score": 94.0, "retrieval": 92.0}, {"overall_score": 80.0, "retrieval": 82.0}, threshold=5.0)

    assert result.passed is False
    assert result.quality_drop == 14.0
    assert "overall_score_drop:14.0" in result.failures
    assert "retrieval_drop:10.0" in result.failures


def test_benchmark_suite_loads_json_dataset(tmp_path):
    dataset = tmp_path / "benchmark.json"
    dataset.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "question": "Find lead",
                        "expected_retrieval": ["lead prefers email"],
                        "retrieved_chunks": [{"content": "lead prefers email", "score": 0.95}],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    suite = BenchmarkSuite()

    cases = suite.load_dataset(dataset, "rag")

    assert len(cases) == 1
    assert cases[0].question == "Find lead"


def test_retrieval_benchmark_scores_recall_precision():
    async def run():
        suite = BenchmarkSuite()
        suite.register_benchmark(
            "rag_smoke",
            "rag",
            [
                {
                    "question": "What does the lead prefer?",
                    "expected_retrieval": ["email follow-up"],
                    "retrieved_chunks": [{"content": "The lead prefers email follow-up.", "score": 0.94}],
                }
            ],
        )
        return await suite.run_benchmark("rag_smoke")

    result = asyncio.run(run())

    assert result.score == 98.5
    assert result.status == "PASS"
