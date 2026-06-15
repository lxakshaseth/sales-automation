import pytest


@pytest.mark.asyncio
@pytest.mark.unit
async def test_top_k_retrieval_returns_most_relevant_chunk(seeded_vector_db, fake_embedding_generator):
    query_vector = await fake_embedding_generator.embed_text("WhatsApp CRM pricing follow-up automation")

    results = await seeded_vector_db.search(query_vector, top_k=2)

    assert len(results) == 2
    assert results[0]["document_id"] == "doc-sales"
    assert results[0]["score"] >= results[1]["score"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_irrelevant_chunk_filtering_with_threshold(seeded_vector_db, fake_embedding_generator):
    query_vector = await fake_embedding_generator.embed_text("WhatsApp CRM pricing follow-up automation")
    results = await seeded_vector_db.search(query_vector, top_k=3)
    filtered = [result for result in results if result["score"] >= 0.75]

    assert all("cafeteria" not in result["content"].casefold() for result in filtered)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_hinglish_query_retrieval(seeded_vector_db, fake_embedding_generator):
    query_vector = await fake_embedding_generator.embed_text("WhatsApp pricing ka follow up")

    results = await seeded_vector_db.search(query_vector, top_k=1)

    assert results
    assert "WhatsApp" in results[0]["content"]

