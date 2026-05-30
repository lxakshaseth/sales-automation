from app.core.logger import log_event
from app.intelligence.evaluation.models import BenchmarkCase, BenchmarkCategory, EvaluationResult, EvaluationStatus, RetrievalMetrics


class RetrievalEvaluator:
    def evaluate_retrieval(self, cases: list[BenchmarkCase], *, top_k: int = 5) -> EvaluationResult:
        metrics = RetrievalMetrics(
            recall_at_k=self.calculate_recall(cases, top_k=top_k),
            precision_at_k=self.calculate_precision(cases, top_k=top_k),
            retrieval_relevance=self.evaluate_chunk_quality(cases),
            chunk_usefulness=self.evaluate_chunk_quality(cases),
            reranker_quality=self.evaluate_reranker_quality(cases),
        )
        score = round((metrics.recall_at_k * 35 + metrics.precision_at_k * 25 + metrics.retrieval_relevance * 25 + metrics.reranker_quality * 15), 2)
        status = EvaluationStatus.PASS if score >= 90 else EvaluationStatus.WARNING if score >= 75 else EvaluationStatus.FAIL
        log_event("retrieval_metrics", recall_at_k=metrics.recall_at_k, precision_at_k=metrics.precision_at_k, score=score)
        return EvaluationResult(
            name="retrieval_evaluation",
            category=BenchmarkCategory.RAG,
            score=score,
            status=status,
            passed=status != EvaluationStatus.FAIL,
            metrics=metrics.model_dump(),
            case_count=len(cases),
            failures=[case.question for case in cases if case.expected_retrieval and not case.retrieved_chunks],
        )

    def calculate_recall(self, cases: list[BenchmarkCase], *, top_k: int = 5) -> float:
        expected_total = 0
        matched_total = 0
        for case in cases:
            expected = {item.lower() for item in case.expected_retrieval}
            retrieved = " ".join(str(chunk.get("content") or chunk.get("text") or chunk) for chunk in case.retrieved_chunks[:top_k]).lower()
            expected_total += len(expected)
            matched_total += sum(1 for item in expected if item in retrieved)
        return round(matched_total / expected_total, 4) if expected_total else 1.0

    def calculate_precision(self, cases: list[BenchmarkCase], *, top_k: int = 5) -> float:
        scored_chunks = [chunk for case in cases for chunk in case.retrieved_chunks[:top_k]]
        if not scored_chunks:
            return 1.0 if not any(case.expected_retrieval for case in cases) else 0.0
        relevant = sum(1 for chunk in scored_chunks if float(chunk.get("score", chunk.get("relevance", 0.0)) or 0.0) >= 0.65)
        return round(relevant / len(scored_chunks), 4)

    def evaluate_chunk_quality(self, cases: list[BenchmarkCase]) -> float:
        scores = [float(chunk.get("score", chunk.get("relevance", 0.0)) or 0.0) for case in cases for chunk in case.retrieved_chunks]
        return round(sum(scores) / len(scores), 4) if scores else 0.0

    def evaluate_reranker_quality(self, cases: list[BenchmarkCase]) -> float:
        ordered_cases = [case for case in cases if case.retrieved_chunks]
        if not ordered_cases:
            return 0.0
        good_order = 0
        for case in ordered_cases:
            scores = [float(chunk.get("score", 0.0) or 0.0) for chunk in case.retrieved_chunks]
            if scores == sorted(scores, reverse=True):
                good_order += 1
        return round(good_order / len(ordered_cases), 4)
