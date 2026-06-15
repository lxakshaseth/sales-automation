from statistics import mean

from app.core.logger import log_error, log_event
from app.intelligence.evaluation.benchmark_suite import BenchmarkSuite
from app.intelligence.evaluation.models import (
    BenchmarkResult,
    DeploymentDecision,
    DeploymentStatus,
    EvaluationReport,
    EvaluationStatus,
    LatencyMetrics,
    RegressionResult,
    TokenMetrics,
)
from app.intelligence.evaluation.regression_tests import RegressionEvaluator


class EvalRunner:
    def __init__(self, benchmark_suite: BenchmarkSuite | None = None, regression_evaluator: RegressionEvaluator | None = None) -> None:
        self.benchmark_suite = benchmark_suite or BenchmarkSuite()
        self.regression_evaluator = regression_evaluator or RegressionEvaluator()

    async def run_all_evaluations(self, *, baseline: dict[str, float] | None = None) -> EvaluationReport:
        try:
            log_event("evaluation_run_started", benchmark_count=len(self.benchmark_suite.benchmarks))
            benchmarks = await self.run_benchmark_suite()
            overall = self.calculate_overall_score(benchmarks)
            regression = self.regression_evaluator.run_regression_tests(baseline, {"overall_score": overall}) if baseline else None
            decision = self.determine_deployment_status(overall, benchmarks, regression)
            report = self.generate_eval_report(benchmarks, decision, regression)
            log_event("evaluation_run_completed", overall_score=overall, deployment_status=decision.deployment_status.value)
            return report
        except Exception as exc:
            log_error("Evaluation run failed", exc_info=True, error_type=type(exc).__name__)
            decision = DeploymentDecision(
                overall_score=0.0,
                deployment_status=DeploymentStatus.REJECTED,
                approved=False,
                reasons=["evaluation_run_failed"],
                blocking_failures=[str(exc)],
            )
            return EvaluationReport(overall_score=0.0, deployment_decision=decision, recommendations=["Fix evaluation framework failure before deployment."])

    async def run_benchmark_suite(self) -> list[BenchmarkResult]:
        return await self.benchmark_suite.run_all()

    def calculate_overall_score(self, benchmarks: list[BenchmarkResult]) -> float:
        if not benchmarks:
            return 0.0
        return round(mean(result.score for result in benchmarks), 2)

    def generate_eval_report(
        self,
        benchmarks: list[BenchmarkResult],
        decision: DeploymentDecision,
        regression: RegressionResult | None = None,
    ) -> EvaluationReport:
        metrics_summary = {
            "benchmark_count": len(benchmarks),
            "failed_benchmarks": [benchmark.benchmark_name for benchmark in benchmarks if benchmark.status == EvaluationStatus.FAIL],
            "latency": self._latency_metrics(benchmarks).model_dump(),
            "tokens": self._token_metrics(benchmarks).model_dump(),
        }
        recommendations = []
        if decision.deployment_status == DeploymentStatus.REJECTED:
            recommendations.append("Block deployment until failed benchmarks and regressions are resolved.")
        elif decision.deployment_status == DeploymentStatus.WARNING:
            recommendations.append("Deploy only with monitoring and rollback plan.")
        else:
            recommendations.append("Deployment approved by evaluation gates.")
        return EvaluationReport(
            overall_score=decision.overall_score,
            deployment_decision=decision,
            benchmark_results=benchmarks,
            regression_result=regression,
            metrics_summary=metrics_summary,
            recommendations=recommendations,
        )

    def determine_deployment_status(
        self,
        overall_score: float,
        benchmarks: list[BenchmarkResult] | None = None,
        regression: RegressionResult | None = None,
    ) -> DeploymentDecision:
        blocking = []
        if benchmarks:
            blocking.extend(benchmark.benchmark_name for benchmark in benchmarks if benchmark.status == EvaluationStatus.FAIL)
        if regression and not regression.passed:
            blocking.extend(regression.failures)
        if blocking or overall_score < 75:
            status = DeploymentStatus.REJECTED
        elif overall_score < 90:
            status = DeploymentStatus.WARNING
        else:
            status = DeploymentStatus.APPROVED
        return DeploymentDecision(
            overall_score=overall_score,
            deployment_status=status,
            approved=status == DeploymentStatus.APPROVED,
            reasons=[f"overall_score={overall_score}", f"gate={status.value}"],
            blocking_failures=blocking,
        )

    def _latency_metrics(self, benchmarks: list[BenchmarkResult]) -> LatencyMetrics:
        latencies = [float(result.report.get("avg_latency_ms", 0.0)) for result in benchmarks if isinstance(result.report, dict) and result.report.get("avg_latency_ms")]
        if not latencies:
            return LatencyMetrics()
        sorted_latencies = sorted(latencies)
        p95_index = min(len(sorted_latencies) - 1, int(len(sorted_latencies) * 0.95))
        return LatencyMetrics(avg_latency_ms=round(mean(latencies), 2), p95_latency_ms=sorted_latencies[p95_index], max_latency_ms=max(latencies))

    def _token_metrics(self, benchmarks: list[BenchmarkResult]) -> TokenMetrics:
        reductions = [float(result.report.get("token_reduction", 0.0)) for result in benchmarks if isinstance(result.report, dict) and result.report.get("token_reduction")]
        return TokenMetrics(token_reduction=round(mean(reductions), 2) if reductions else 0.0)


async def run_all_evaluations(*, benchmark_suite: BenchmarkSuite | None = None, baseline: dict[str, float] | None = None) -> EvaluationReport:
    return await EvalRunner(benchmark_suite=benchmark_suite).run_all_evaluations(baseline=baseline)
