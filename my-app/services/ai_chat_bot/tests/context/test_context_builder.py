import pytest

from app.context.context_builder import ContextBuilder
from app.models.context_models import TokenBudget


@pytest.mark.asyncio
@pytest.mark.unit
async def test_context_builder_merges_rag_and_memory(retrieved_chunks, chat_messages, small_token_budget):
    result = await ContextBuilder().build_context(
        user_query="What should I tell Akshat about WhatsApp CRM pricing?",
        retrieved_context=retrieved_chunks,
        short_term_memory=chat_messages,
        long_term_memory={"content": "Akshat prefers professional Hinglish.", "importance": 0.8},
        summarized_memory=[{"summary": "Earlier discussion covered CRM integration."}],
        token_budget=small_token_budget,
        language_hint="Hinglish",
    )

    assert result.final_prompt
    assert result.messages[0]["role"] == "system"
    assert result.retrieved_context
    assert result.short_term_memory
    assert result.token_usage["prompt_tokens"] <= small_token_budget.max_context_tokens


@pytest.mark.asyncio
@pytest.mark.unit
async def test_context_builder_filters_duplicate_retrieval(small_token_budget):
    duplicate = {"content": "Same RAG chunk", "score": 0.9, "chunk_id": "a", "document_id": "d"}

    result = await ContextBuilder().build_context(
        user_query="Same RAG chunk?",
        retrieved_context=[duplicate, duplicate | {"chunk_id": "b"}],
        token_budget=small_token_budget,
    )

    assert len(result.retrieved_context) == 1
    assert any("dropped_duplicates" in warning for warning in result.semantic_metadata.warnings)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_prompt_overflow_prevention_drops_low_priority_context():
    budget = TokenBudget(
        model_name="gpt-4o-mini",
        max_context_tokens=512,
        reserved_response_tokens=128,
        system_prompt_tokens=120,
    )
    long_context = [{"content": " ".join(["low priority unrelated text"] * 500), "score": 0.1, "chunk_id": "c", "document_id": "d"}]

    result = await ContextBuilder().build_context(
        user_query="pricing",
        retrieved_context=long_context,
        token_budget=budget,
    )

    assert result.token_usage["context_tokens"] <= budget.available_context_tokens
