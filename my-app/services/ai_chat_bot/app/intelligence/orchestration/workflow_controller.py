import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any

from app.core.logger import log_error, log_event
from app.intelligence.orchestration.exceptions import OrchestrationTimeoutError, WorkflowExecutionError
from app.intelligence.orchestration.models import ExecutionTrace, WorkflowStatus

WorkflowStep = Callable[[], Awaitable[Any]]


class WorkflowController:
    """Sequences workflow steps with retries, timeout handling, and traces."""

    def __init__(self, retry_limit: int = 1, timeout_seconds: float = 30.0) -> None:
        self.retry_limit = retry_limit
        self.timeout_seconds = timeout_seconds

    async def execute_workflow(self, steps: list[tuple[str, WorkflowStep]]) -> tuple[dict[str, Any], list[ExecutionTrace]]:
        results: dict[str, Any] = {}
        traces: list[ExecutionTrace] = []
        for name, step in steps:
            started = time.perf_counter()
            try:
                results[name] = await asyncio.wait_for(self.retry_step(name, step), timeout=self.timeout_seconds)
                traces.append(ExecutionTrace(step=name, status=WorkflowStatus.COMPLETED, duration_ms=round((time.perf_counter() - started) * 1000, 2)))
                log_event("workflow_step_completed", step=name, duration_ms=traces[-1].duration_ms)
            except TimeoutError as exc:
                trace = ExecutionTrace(step=name, status=WorkflowStatus.FAILED, duration_ms=round((time.perf_counter() - started) * 1000, 2), error="timeout")
                traces.append(trace)
                log_error("workflow_step_timeout", step=name, exc_info=True)
                raise OrchestrationTimeoutError(f"workflow step timed out: {name}") from exc
            except Exception as exc:
                trace = ExecutionTrace(step=name, status=WorkflowStatus.FAILED, duration_ms=round((time.perf_counter() - started) * 1000, 2), error=str(exc))
                traces.append(trace)
                log_error("workflow_step_failed", step=name, error_type=type(exc).__name__, exc_info=True)
                raise WorkflowExecutionError(f"workflow step failed: {name}") from exc
        return results, traces

    async def retry_step(self, name: str, step: WorkflowStep) -> Any:
        last_error: Exception | None = None
        for attempt in range(self.retry_limit + 1):
            try:
                if attempt:
                    log_event("workflow_retry_attempt", step=name, attempt=attempt)
                    await asyncio.sleep(min(0.25 * attempt, 1.0))
                return await step()
            except Exception as exc:
                last_error = exc
        raise WorkflowExecutionError(str(last_error) if last_error else f"step failed: {name}")

    def abort_workflow(self, reason: str) -> ExecutionTrace:
        log_error("workflow_aborted", reason=reason)
        return ExecutionTrace(step="abort_workflow", status=WorkflowStatus.ABORTED, error=reason)

    def recover_workflow(self, reason: str) -> dict[str, str]:
        log_event("workflow_recovery_started", reason=reason)
        return {"response": "I could not complete the request safely.", "reason": reason}
