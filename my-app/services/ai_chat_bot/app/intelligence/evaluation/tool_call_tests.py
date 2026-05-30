from app.core.logger import log_event
from app.intelligence.evaluation.models import BenchmarkCase, BenchmarkCategory, EvaluationResult, EvaluationStatus, ToolMetrics


class ToolCallEvaluator:
    def evaluate_tool_calls(self, cases: list[BenchmarkCase]) -> EvaluationResult:
        metrics = ToolMetrics(
            tool_selection_accuracy=self.verify_tool_selection(cases),
            parameter_extraction_accuracy=self.verify_parameters(cases),
            execution_success_rate=self._execution_success_rate(cases),
            hallucinated_tool_call_rate=self._hallucinated_tool_rate(cases),
        )
        score = round(
            metrics.tool_selection_accuracy * 35
            + metrics.parameter_extraction_accuracy * 25
            + metrics.execution_success_rate * 25
            + (1.0 - metrics.hallucinated_tool_call_rate) * 15,
            2,
        )
        status = EvaluationStatus.PASS if score >= 90 else EvaluationStatus.WARNING if score >= 75 else EvaluationStatus.FAIL
        log_event("tool_metrics", tool_accuracy=metrics.tool_selection_accuracy, execution_success_rate=metrics.execution_success_rate, score=score)
        return EvaluationResult(
            name="tool_call_evaluation",
            category=BenchmarkCategory.TOOL_CALLING,
            score=score,
            status=status,
            passed=status != EvaluationStatus.FAIL,
            metrics=metrics.model_dump(),
            case_count=len(cases),
            failures=[case.question for case in cases if case.expected_tool and case.actual_tool != case.expected_tool],
        )

    def verify_tool_selection(self, cases: list[BenchmarkCase]) -> float:
        expected = [case for case in cases if case.expected_tool]
        if not expected:
            return 1.0
        return round(sum(1 for case in expected if case.actual_tool == case.expected_tool) / len(expected), 4)

    def verify_parameters(self, cases: list[BenchmarkCase]) -> float:
        parameter_cases = [case for case in cases if case.expected_parameters]
        if not parameter_cases:
            return 1.0
        passed = 0
        for case in parameter_cases:
            if all(case.actual_parameters.get(key) == value for key, value in case.expected_parameters.items()):
                passed += 1
        return round(passed / len(parameter_cases), 4)

    def measure_tool_accuracy(self, cases: list[BenchmarkCase]) -> float:
        return self.evaluate_tool_calls(cases).score / 100

    def _execution_success_rate(self, cases: list[BenchmarkCase]) -> float:
        tool_cases = [case for case in cases if case.expected_tool]
        if not tool_cases:
            return 1.0
        return round(sum(1 for case in tool_cases if case.tool_success is True) / len(tool_cases), 4)

    def _hallucinated_tool_rate(self, cases: list[BenchmarkCase]) -> float:
        if not cases:
            return 0.0
        hallucinated = sum(1 for case in cases if not case.expected_tool and case.actual_tool)
        fake_confirmations = sum(1 for case in cases if case.expected_tool and case.tool_success is not True and case.actual_answer and "success" in case.actual_answer.lower())
        return round((hallucinated + fake_confirmations) / len(cases), 4)
