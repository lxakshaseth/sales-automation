import os
import time
from typing import Any

from app.core.logger import log_error, log_event
from app.intelligence.optimization.cache_optimizer import CacheOptimizer
from app.intelligence.optimization.context_compressor import ContextCompressor
from app.intelligence.optimization.exceptions import TokenCounterError
from app.intelligence.optimization.memory_summarizer import MemorySummarizer
from app.intelligence.optimization.models import (
    ContextMetrics,
    ContextPriority,
    OptimizationReport,
    OptimizedContext,
    TokenAllocation,
    TokenBudget,
    TokenUsage,
)
from app.intelligence.optimization.prompt_optimizer import PromptOptimizer
from app.utils.token_helpers import estimate_tokens, trim_text_to_token_limit


class TokenOptimizer:
    """Central token optimization orchestrator and budget authority."""

    def __init__(
        self,
        budget: TokenBudget | None = None,
        compressor: ContextCompressor | None = None,
        summarizer: MemorySummarizer | None = None,
        prompt_optimizer: PromptOptimizer | None = None,
        cache_optimizer: CacheOptimizer | None = None,
    ) -> None:
        self.budget = budget or self._budget_from_env()
        self.compressor = compressor or ContextCompressor()
        self.summarizer = summarizer or MemorySummarizer()
        self.prompt_optimizer = prompt_optimizer or PromptOptimizer()
        self.cache_optimizer = cache_optimizer or CacheOptimizer()

    def count_tokens(self, value: Any, *, model_name: str | None = None) -> int:
        try:
            if isinstance(value, list):
                return sum(self.count_tokens(item, model_name=model_name) for item in value)
            if isinstance(value, dict):
                return estimate_tokens(str(value.get("content") or value.get("text") or value.get("message") or value), model_name=model_name)
            return estimate_tokens(str(value or ""), model_name=model_name)
        except Exception as exc:
            log_error("Token counting failed", exc_info=True, error_type=type(exc).__name__)
            raise TokenCounterError("token counting failed") from exc

    def validate_token_budget(self, usage: TokenUsage, budget: TokenBudget | None = None) -> bool:
        resolved_budget = budget or self.budget
        valid = (
            usage.total_tokens <= resolved_budget.available_input_tokens
            and usage.rag_tokens <= resolved_budget.max_rag_tokens
            and usage.history_tokens <= resolved_budget.max_history_tokens
            and usage.tool_output_tokens <= resolved_budget.max_tool_output_tokens
            and usage.system_prompt_tokens <= resolved_budget.max_system_prompt_tokens
        )
        if not valid:
            log_event("token_budget_overflow_detected", total_tokens=usage.total_tokens, max_input_tokens=resolved_budget.available_input_tokens)
        return valid

    async def optimize_context(self, raw_context: dict[str, Any], *, budget: TokenBudget | None = None) -> OptimizedContext:
        started_at = time.perf_counter()
        resolved_budget = budget or self.budget
        try:
            log_event("token_optimization_started", max_context_tokens=resolved_budget.max_context_tokens)
            cache_key = self.cache_optimizer.build_cache_key(str(raw_context), namespace="context")
            cached = await self.cache_optimizer.get_cached_context(cache_key)
            if isinstance(cached, OptimizedContext):
                return cached

            system_prompt = self.prompt_optimizer.optimize_prompt(str(raw_context.get("system_prompt") or ""))
            user_query = str(raw_context.get("user_query") or raw_context.get("query") or "").strip()
            if not user_query:
                user_query = "No user query supplied."

            rag_context = list(raw_context.get("rag_context") or raw_context.get("retrieval_results") or [])
            history = list(raw_context.get("history") or raw_context.get("messages") or [])
            tool_outputs = self._compress_tool_outputs(list(raw_context.get("tool_outputs") or []))

            original_usage = self._build_usage(system_prompt, user_query, rag_context, history, "", tool_outputs, resolved_budget)
            rag_result = self.compressor.optimize_rag_context(rag_context, token_limit=resolved_budget.max_rag_tokens, model_name=resolved_budget.model_name)
            history_result = self.compressor.optimize_history(history, token_limit=resolved_budget.max_history_tokens, model_name=resolved_budget.model_name)
            memory_summary = await self.summarizer.summarize_history(
                history,
                token_limit=max(200, min(1000, resolved_budget.max_history_tokens // 3 or 200)),
                model_name=resolved_budget.model_name,
            )

            optimized_system = trim_text_to_token_limit(system_prompt, resolved_budget.max_system_prompt_tokens, model_name=resolved_budget.model_name)
            optimized_tools = self._trim_tool_outputs(tool_outputs, resolved_budget.max_tool_output_tokens, resolved_budget.model_name)
            optimized_rag = rag_result.output if isinstance(rag_result.output, list) else []
            optimized_history = history_result.output if isinstance(history_result.output, list) else []

            usage = self._build_usage(
                optimized_system,
                user_query,
                optimized_rag,
                optimized_history,
                memory_summary.summary,
                optimized_tools,
                resolved_budget,
            )
            overflow_prevented = original_usage.total_tokens > resolved_budget.available_input_tokens
            if not self.validate_token_budget(usage, resolved_budget):
                optimized_history = []
                optimized_rag = self.trim_context(optimized_rag, resolved_budget.max_rag_tokens // 2, model_name=resolved_budget.model_name)
                usage = self._build_usage(optimized_system, user_query, optimized_rag, optimized_history, memory_summary.summary, optimized_tools, resolved_budget)
                overflow_prevented = True

            final_prompt = self._build_final_prompt(optimized_system, user_query, optimized_rag, memory_summary.summary, optimized_tools)
            if self.count_tokens(final_prompt, model_name=resolved_budget.model_name) > resolved_budget.available_input_tokens:
                final_prompt = trim_text_to_token_limit(final_prompt, resolved_budget.available_input_tokens, model_name=resolved_budget.model_name)
                overflow_prevented = True

            final_tokens = self.count_tokens(final_prompt, model_name=resolved_budget.model_name)
            report = self.build_token_report(
                original_tokens=max(original_usage.total_tokens, self.count_tokens(str(raw_context), model_name=resolved_budget.model_name)),
                optimized_tokens=final_tokens,
                usage=usage,
                overflow_prevented=overflow_prevented,
                metrics=ContextMetrics(
                    rag_chunk_count=len(optimized_rag),
                    history_message_count=len(optimized_history),
                    tool_output_count=len(optimized_tools),
                    duplicate_count=rag_result.duplicate_removed + history_result.duplicate_removed,
                    dropped_low_value_chunks=max(0, len(rag_context) - len(optimized_rag)),
                    trimmed_sections=self._trimmed_sections(original_usage, usage, resolved_budget),
                ),
            )
            result = OptimizedContext(
                system_prompt=optimized_system,
                user_query=user_query,
                rag_context=optimized_rag,
                history=optimized_history,
                memory_summary=memory_summary.summary,
                tool_outputs=optimized_tools,
                final_prompt=final_prompt,
                report=report,
                metadata=raw_context.get("metadata", {}),
            )
            await self.cache_optimizer.cache_optimization(cache_key, result)
            log_event(
                "token_optimization_completed",
                original_tokens=report.original_tokens,
                optimized_tokens=report.optimized_tokens,
                saved_tokens=report.saved_tokens,
                compression_ratio=report.compression_ratio,
                latency_ms=round((time.perf_counter() - started_at) * 1000, 2),
            )
            return result
        except Exception as exc:
            log_error("Token optimization failed; using safe fallback", exc_info=True, error_type=type(exc).__name__)
            if isinstance(exc, TokenCounterError):
                raise
            return self._safe_fallback(raw_context, resolved_budget)

    def trim_context(self, context: list[dict[str, Any]], token_limit: int, *, model_name: str | None = None) -> list[dict[str, Any]]:
        trimmed = []
        used = 0
        for item in context:
            text = str(item.get("content") or item.get("text") or item)
            tokens = self.count_tokens(text, model_name=model_name)
            if used + tokens <= token_limit:
                trimmed.append(item)
                used += tokens
        log_event("context_trimmed", retained_items=len(trimmed), token_limit=token_limit)
        return trimmed

    def build_token_report(
        self,
        *,
        original_tokens: int,
        optimized_tokens: int,
        usage: TokenUsage,
        overflow_prevented: bool = False,
        fallback_used: bool = False,
        metrics: ContextMetrics | None = None,
    ) -> OptimizationReport:
        saved = max(0, original_tokens - optimized_tokens)
        return OptimizationReport(
            original_tokens=original_tokens,
            optimized_tokens=optimized_tokens,
            saved_tokens=saved,
            compression_ratio=round((saved / original_tokens) * 100, 2) if original_tokens else 0.0,
            overflow_prevented=overflow_prevented,
            fallback_used=fallback_used,
            token_usage=usage,
            allocations=self._allocations(usage),
            metrics=metrics or ContextMetrics(),
        )

    def _budget_from_env(self) -> TokenBudget:
        return TokenBudget(
            max_context_tokens=int(os.getenv("MAX_CONTEXT_TOKENS", "12000")),
            max_rag_tokens=int(os.getenv("MAX_RAG_TOKENS", "4000")),
            max_history_tokens=int(os.getenv("MAX_HISTORY_TOKENS", "3000")),
            max_tool_output_tokens=int(os.getenv("MAX_TOOL_OUTPUT_TOKENS", "1000")),
            max_system_prompt_tokens=int(os.getenv("MAX_SYSTEM_PROMPT_TOKENS", "1000")),
            reserved_response_tokens=int(os.getenv("RESERVED_RESPONSE_TOKENS", "1000")),
            model_name=os.getenv("TOKEN_OPTIMIZER_MODEL"),
        )

    def _build_usage(
        self,
        system_prompt: str,
        user_query: str,
        rag_context: list[dict[str, Any]],
        history: list[dict[str, Any]],
        memory_summary: str,
        tool_outputs: list[dict[str, Any]],
        budget: TokenBudget,
    ) -> TokenUsage:
        return TokenUsage(
            system_prompt_tokens=self.count_tokens(system_prompt, model_name=budget.model_name),
            user_query_tokens=self.count_tokens(user_query, model_name=budget.model_name),
            rag_tokens=self.count_tokens(rag_context, model_name=budget.model_name),
            history_tokens=self.count_tokens(history, model_name=budget.model_name),
            memory_summary_tokens=self.count_tokens(memory_summary, model_name=budget.model_name),
            tool_output_tokens=self.count_tokens(tool_outputs, model_name=budget.model_name),
        )

    def _compress_tool_outputs(self, outputs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        compact = []
        for output in outputs:
            compact.append(
                {
                    key: value
                    for key, value in output.items()
                    if key in {"success", "status", "id", "lead_id", "event_id", "email_id", "error", "result"} and value is not None
                }
            )
        log_event("tool_outputs_compressed", original_count=len(outputs), compressed_count=len(compact))
        return compact

    def _trim_tool_outputs(self, outputs: list[dict[str, Any]], token_limit: int, model_name: str | None) -> list[dict[str, Any]]:
        return self.trim_context(outputs, token_limit, model_name=model_name)

    def _build_final_prompt(
        self,
        system_prompt: str,
        user_query: str,
        rag_context: list[dict[str, Any]],
        memory_summary: str,
        tool_outputs: list[dict[str, Any]],
    ) -> str:
        return "\n\n".join(
            part
            for part in [
                f"System:\n{system_prompt}" if system_prompt else "",
                f"Current User Query:\n{user_query}",
                f"Tool Outputs:\n{tool_outputs}" if tool_outputs else "",
                f"Retrieval Context:\n{rag_context}" if rag_context else "",
                f"Memory Summary:\n{memory_summary}" if memory_summary else "",
            ]
            if part
        )

    def _allocations(self, usage: TokenUsage) -> list[TokenAllocation]:
        return [
            TokenAllocation(priority=ContextPriority.SYSTEM_PROMPT, token_limit=self.budget.max_system_prompt_tokens, allocated_tokens=usage.system_prompt_tokens),
            TokenAllocation(priority=ContextPriority.CURRENT_USER_QUERY, token_limit=self.budget.available_input_tokens, allocated_tokens=usage.user_query_tokens),
            TokenAllocation(priority=ContextPriority.TOOL_OUTPUTS, token_limit=self.budget.max_tool_output_tokens, allocated_tokens=usage.tool_output_tokens),
            TokenAllocation(priority=ContextPriority.RETRIEVAL_RESULTS, token_limit=self.budget.max_rag_tokens, allocated_tokens=usage.rag_tokens),
            TokenAllocation(priority=ContextPriority.MEMORY_SUMMARY, token_limit=self.budget.max_history_tokens, allocated_tokens=usage.memory_summary_tokens),
            TokenAllocation(priority=ContextPriority.HISTORICAL_MESSAGES, token_limit=self.budget.max_history_tokens, allocated_tokens=usage.history_tokens),
        ]

    def _trimmed_sections(self, original: TokenUsage, optimized: TokenUsage, budget: TokenBudget) -> list[str]:
        sections = []
        if original.rag_tokens > optimized.rag_tokens or optimized.rag_tokens > budget.max_rag_tokens:
            sections.append("retrieval_results")
        if original.history_tokens > optimized.history_tokens or optimized.history_tokens > budget.max_history_tokens:
            sections.append("historical_messages")
        if original.tool_output_tokens > optimized.tool_output_tokens or optimized.tool_output_tokens > budget.max_tool_output_tokens:
            sections.append("tool_outputs")
        if original.system_prompt_tokens > optimized.system_prompt_tokens:
            sections.append("system_prompt")
        return sections

    def _safe_fallback(self, raw_context: dict[str, Any], budget: TokenBudget) -> OptimizedContext:
        user_query = str(raw_context.get("user_query") or raw_context.get("query") or "No user query supplied.")
        final_prompt = trim_text_to_token_limit(user_query, budget.available_input_tokens, model_name=budget.model_name)
        usage = TokenUsage(user_query_tokens=self.count_tokens(final_prompt, model_name=budget.model_name))
        report = self.build_token_report(
            original_tokens=self.count_tokens(str(raw_context), model_name=budget.model_name),
            optimized_tokens=usage.total_tokens,
            usage=usage,
            overflow_prevented=True,
            fallback_used=True,
            metrics=ContextMetrics(trimmed_sections=["fallback_user_query_only"]),
        )
        return OptimizedContext(user_query=user_query, final_prompt=final_prompt, report=report)


async def optimize_context(raw_context: dict[str, Any], *, budget: TokenBudget | None = None) -> OptimizedContext:
    return await TokenOptimizer(budget=budget).optimize_context(raw_context, budget=budget)
