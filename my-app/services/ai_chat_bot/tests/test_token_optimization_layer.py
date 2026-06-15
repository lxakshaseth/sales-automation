import asyncio

from app.intelligence.optimization import ContextCompressor, PromptOptimizer, TokenBudget, TokenOptimizer


def test_prompt_optimizer_removes_duplicate_instructions():
    optimizer = PromptOptimizer()

    optimized = optimizer.optimize_prompt("Do this\nDo this\n\nPlease make sure to respond briefly.")

    assert optimized.count("Do this") == 1
    assert "Do respond briefly." in optimized


def test_rag_context_compression_deduplicates_and_drops_low_score_chunks():
    compressor = ContextCompressor()

    result = compressor.optimize_rag_context(
        [
            {"content": "Lead wants CRM automation and email follow up.", "score": 0.95},
            {"content": "Lead wants CRM automation and email follow up.", "score": 0.93},
            {"content": "Unrelated low value text.", "score": 0.45},
        ],
        token_limit=100,
    )

    assert result.success is True
    assert result.duplicate_removed == 1
    assert len(result.output) == 1
    assert result.saved_tokens > 0


def test_token_optimizer_prevents_overflow_and_builds_report():
    async def run():
        budget = TokenBudget(
            max_context_tokens=512,
            max_rag_tokens=40,
            max_history_tokens=40,
            max_tool_output_tokens=30,
            max_system_prompt_tokens=30,
            reserved_response_tokens=128,
        )
        raw_context = {
            "system_prompt": "You are a sales assistant.\nYou are a sales assistant.",
            "user_query": "Follow up with the CRM lead.",
            "rag_context": [
                {"content": "Lead asked for CRM automation. " * 20, "score": 0.95},
                {"content": "Lead asked for CRM automation. " * 20, "score": 0.94},
                {"content": "Low value unrelated chunk.", "score": 0.20},
            ],
            "history": [
                {"role": "user", "content": "My budget is 10000 and I need email automation. " * 10},
                {"role": "assistant", "content": "hello"},
            ],
            "tool_outputs": [{"success": True, "lead_id": "123", "result": {"status": "qualified"}, "raw": "x" * 5000}],
        }
        return await TokenOptimizer(budget).optimize_context(raw_context)

    optimized = asyncio.run(run())

    assert optimized.report.optimized_tokens <= 384
    assert optimized.report.saved_tokens > 0
    assert optimized.report.metrics.duplicate_count >= 1
    assert optimized.report.metrics.dropped_low_value_chunks >= 1
    assert optimized.tool_outputs == [{"success": True, "lead_id": "123", "result": {"status": "qualified"}}]


def test_token_report_matches_required_shape():
    optimizer = TokenOptimizer(TokenBudget(max_context_tokens=512))
    usage = optimizer._build_usage("", "hello", [], [], "", [], optimizer.budget)

    report = optimizer.build_token_report(original_tokens=14500, optimized_tokens=7800, usage=usage)

    assert report.original_tokens == 14500
    assert report.optimized_tokens == 7800
    assert report.saved_tokens == 6700
    assert report.compression_ratio == 46.21
