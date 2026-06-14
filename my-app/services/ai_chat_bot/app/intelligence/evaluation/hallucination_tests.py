from app.core.logger import log_event
from app.intelligence.evaluation.models import BenchmarkCase, BenchmarkCategory, EvaluationResult, EvaluationStatus, HallucinationMetrics


class HallucinationEvaluator:
    def evaluate_hallucinations(self, cases: list[BenchmarkCase]) -> EvaluationResult:
        metrics = self._metrics(cases)
        score = round((1.0 - metrics.hallucination_rate) * 55 + metrics.source_grounding_accuracy * 30 + metrics.confidence_alignment * 15, 2)
        status = EvaluationStatus.PASS if score >= 90 else EvaluationStatus.WARNING if score >= 75 else EvaluationStatus.FAIL
        log_event("hallucination_metrics", hallucination_rate=metrics.hallucination_rate, score=score)
        return EvaluationResult(
            name="hallucination_evaluation",
            category=BenchmarkCategory.HALLUCINATION,
            score=score,
            status=status,
            passed=status != EvaluationStatus.FAIL,
            metrics=metrics.model_dump(),
            case_count=len(cases),
            failures=[case.question for case in cases if case.unsupported_claims],
        )

    def calculate_hallucination_rate(self, cases: list[BenchmarkCase]) -> float:
        if not cases:
            return 0.0
        hallucinated = sum(1 for case in cases if case.unsupported_claims)
        return round(hallucinated / len(cases), 4)

    def detect_unsupported_claims(self, case: BenchmarkCase) -> list[str]:
        return case.unsupported_claims

    def score_grounding_quality(self, cases: list[BenchmarkCase]) -> float:
        if not cases:
            return 0.0
        grounded = sum(1 for case in cases if not case.unsupported_claims and (case.retrieved_chunks or case.expected_retrieval or case.tool_success is True))
        return round(grounded / len(cases), 4)

    def _metrics(self, cases: list[BenchmarkCase]) -> HallucinationMetrics:
        unsupported_count = sum(len(case.unsupported_claims) for case in cases)
        confidence_cases = [case for case in cases if case.expected_confidence is not None]
        confidence_alignment = (
            sum(1 for case in confidence_cases if (case.expected_confidence or 0.0) >= 0.60 and not case.unsupported_claims) / len(confidence_cases)
            if confidence_cases
            else 1.0
        )
        return HallucinationMetrics(
            hallucination_rate=self.calculate_hallucination_rate(cases),
            unsupported_claim_count=unsupported_count,
            source_grounding_accuracy=self.score_grounding_quality(cases),
            confidence_alignment=round(confidence_alignment, 4),
        )
