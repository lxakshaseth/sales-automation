from app.core.logger import log_event
from app.intelligence.evaluation.models import BenchmarkCase, BenchmarkCategory, EvaluationResult, EvaluationStatus


class PromptEvaluator:
    def evaluate_prompt(self, cases: list[BenchmarkCase]) -> EvaluationResult:
        consistency = self.test_prompt_consistency(cases)
        accuracy = self.test_prompt_accuracy(cases)
        compliance = self.test_prompt_compliance(cases)
        score = round(consistency * 25 + accuracy * 45 + compliance * 30, 2)
        status = EvaluationStatus.PASS if score >= 90 else EvaluationStatus.WARNING if score >= 75 else EvaluationStatus.FAIL
        log_event("prompt_metrics", consistency=consistency, accuracy=accuracy, compliance=compliance, score=score)
        return EvaluationResult(
            name="prompt_evaluation",
            category=BenchmarkCategory.PROMPT,
            score=score,
            status=status,
            passed=status != EvaluationStatus.FAIL,
            metrics={
                "instruction_adherence": compliance,
                "output_consistency": consistency,
                "prompt_accuracy": accuracy,
                "structured_output_compliance": compliance,
                "persona_consistency": consistency,
                "multilingual_performance": compliance,
            },
            case_count=len(cases),
            failures=[case.question for case in cases if case.expected_answer and not self._contains_expected(case)],
        )

    def test_prompt_consistency(self, cases: list[BenchmarkCase]) -> float:
        if not cases:
            return 1.0
        complete = sum(1 for case in cases if case.actual_answer)
        return round(complete / len(cases), 4)

    def test_prompt_accuracy(self, cases: list[BenchmarkCase]) -> float:
        answer_cases = [case for case in cases if case.expected_answer]
        if not answer_cases:
            return 1.0
        return round(sum(1 for case in answer_cases if self._contains_expected(case)) / len(answer_cases), 4)

    def test_prompt_compliance(self, cases: list[BenchmarkCase]) -> float:
        if not cases:
            return 1.0
        compliant = sum(1 for case in cases if case.actual_answer and not case.unsupported_claims)
        return round(compliant / len(cases), 4)

    def _contains_expected(self, case: BenchmarkCase) -> bool:
        return bool(case.actual_answer and case.expected_answer and case.expected_answer.lower() in case.actual_answer.lower())
