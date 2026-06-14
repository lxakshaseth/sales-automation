from app.core.logger import log_error, log_event
from app.intelligence.evaluation.models import RegressionResult


class RegressionEvaluator:
    def run_regression_tests(self, baseline: dict[str, float], current: dict[str, float], *, threshold: float = 5.0) -> RegressionResult:
        return self.compare_baselines(baseline, current, threshold=threshold)

    def compare_baselines(self, baseline: dict[str, float], current: dict[str, float], *, threshold: float = 5.0) -> RegressionResult:
        baseline_score = float(baseline.get("overall_score", 0.0))
        current_score = float(current.get("overall_score", 0.0))
        quality_drop = self.detect_quality_drop(baseline_score, current_score)
        failures = []
        if quality_drop > threshold:
            failures.append(f"overall_score_drop:{quality_drop}")
        for key, baseline_value in baseline.items():
            if key == "overall_score":
                continue
            drop = float(baseline_value) - float(current.get(key, 0.0))
            if drop > threshold:
                failures.append(f"{key}_drop:{round(drop, 2)}")
        passed = not failures
        if not passed:
            log_error("Regression failure detected", failures=failures, baseline_score=baseline_score, current_score=current_score)
        else:
            log_event("regression_passed", baseline_score=baseline_score, current_score=current_score)
        return RegressionResult(
            passed=passed,
            baseline_score=baseline_score,
            current_score=current_score,
            quality_drop=quality_drop,
            threshold=threshold,
            failures=failures,
        )

    def detect_quality_drop(self, baseline_score: float, current_score: float) -> float:
        return round(max(0.0, baseline_score - current_score), 2)

    def generate_regression_report(self, result: RegressionResult) -> dict:
        return result.model_dump()
