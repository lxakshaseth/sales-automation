import csv
import json
import time
from pathlib import Path
from typing import Any

from app.core.logger import log_error, log_event
from app.intelligence.evaluation.exceptions import BenchmarkDatasetError
from app.intelligence.evaluation.hallucination_tests import HallucinationEvaluator
from app.intelligence.evaluation.models import BenchmarkCase, BenchmarkCategory, BenchmarkResult, EvaluationResult, EvaluationStatus
from app.intelligence.evaluation.prompt_tests import PromptEvaluator
from app.intelligence.evaluation.retrieval_tests import RetrievalEvaluator
from app.intelligence.evaluation.tool_call_tests import ToolCallEvaluator


class BenchmarkSuite:
    def __init__(self) -> None:
        self.benchmarks: dict[str, tuple[BenchmarkCategory, list[BenchmarkCase]]] = {}
        self.prompt_evaluator = PromptEvaluator()
        self.hallucination_evaluator = HallucinationEvaluator()
        self.retrieval_evaluator = RetrievalEvaluator()
        self.tool_evaluator = ToolCallEvaluator()

    def register_benchmark(self, name: str, category: BenchmarkCategory | str, cases: list[BenchmarkCase | dict[str, Any]]) -> None:
        resolved_category = category if isinstance(category, BenchmarkCategory) else BenchmarkCategory(str(category))
        resolved_cases = [case if isinstance(case, BenchmarkCase) else BenchmarkCase(**case) for case in cases]
        self.benchmarks[name] = (resolved_category, resolved_cases)
        log_event("benchmark_registered", benchmark=name, category=resolved_category.value, case_count=len(resolved_cases))

    def load_dataset(self, path: str | Path, category: BenchmarkCategory | str) -> list[BenchmarkCase]:
        dataset_path = Path(path)
        if not dataset_path.exists():
            raise BenchmarkDatasetError(f"benchmark dataset not found: {dataset_path}")
        suffix = dataset_path.suffix.lower()
        if suffix == ".json":
            raw = json.loads(dataset_path.read_text(encoding="utf-8"))
        elif suffix == ".csv":
            with dataset_path.open("r", encoding="utf-8", newline="") as handle:
                raw = list(csv.DictReader(handle))
        elif suffix in {".yaml", ".yml"}:
            raise BenchmarkDatasetError("YAML benchmark datasets are reserved for future support")
        else:
            raise BenchmarkDatasetError(f"unsupported benchmark dataset format: {suffix}")
        cases = raw.get("cases", raw) if isinstance(raw, dict) else raw
        return [BenchmarkCase(**case) for case in cases]

    async def run_benchmark(self, name: str) -> BenchmarkResult:
        started = time.perf_counter()
        if name not in self.benchmarks:
            raise BenchmarkDatasetError(f"benchmark is not registered: {name}")
        category, cases = self.benchmarks[name]
        result = self._evaluate(category, cases)
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        benchmark = BenchmarkResult(
            benchmark_name=name,
            category=category,
            score=result.score,
            status=result.status,
            results=[result],
            case_count=len(cases),
            duration_ms=duration_ms,
            report=result.metrics,
        )
        log_event("benchmark_result", benchmark=name, category=category.value, score=benchmark.score, status=benchmark.status.value, duration_ms=duration_ms)
        return benchmark

    async def run_all(self) -> list[BenchmarkResult]:
        results = []
        for name in self.benchmarks:
            try:
                results.append(await self.run_benchmark(name))
            except Exception as exc:
                log_error("Benchmark execution failed", benchmark=name, error_type=type(exc).__name__, exc_info=True)
                results.append(self._failed_benchmark(name, exc))
        return results

    def _evaluate(self, category: BenchmarkCategory, cases: list[BenchmarkCase]) -> EvaluationResult:
        if category == BenchmarkCategory.PROMPT:
            return self.prompt_evaluator.evaluate_prompt(cases)
        if category == BenchmarkCategory.HALLUCINATION:
            return self.hallucination_evaluator.evaluate_hallucinations(cases)
        if category == BenchmarkCategory.RAG:
            return self.retrieval_evaluator.evaluate_retrieval(cases)
        if category == BenchmarkCategory.TOOL_CALLING:
            return self.tool_evaluator.evaluate_tool_calls(cases)
        return self.prompt_evaluator.evaluate_prompt(cases)

    def _failed_benchmark(self, name: str, exc: Exception) -> BenchmarkResult:
        result = EvaluationResult(
            name=f"{name}_failed",
            category=BenchmarkCategory.REGRESSION,
            score=0.0,
            status=EvaluationStatus.FAIL,
            passed=False,
            failures=[str(exc)],
        )
        return BenchmarkResult(benchmark_name=name, category=BenchmarkCategory.REGRESSION, score=0.0, status=EvaluationStatus.FAIL, results=[result])
