import pytest

from tests.mocks.fake_vector_db import FakeVectorRecord


@pytest.mark.asyncio
@pytest.mark.unit
async def test_vector_insertion_and_similarity_search(fake_vector_db, fake_embedding_generator):
    vector = await fake_embedding_generator.embed_text("WhatsApp CRM automation")
    await fake_vector_db.add(FakeVectorRecord("v1", "c1", "d1", vector, "WhatsApp CRM automation"))

    results = await fake_vector_db.search(vector, top_k=1)

    assert len(results) == 1
    assert results[0]["chunk_id"] == "c1"
    assert results[0]["score"] > 0.99


@pytest.mark.asyncio
@pytest.mark.unit
async def test_duplicate_vector_is_rejected(fake_vector_db, fake_embedding_generator):
    vector = await fake_embedding_generator.embed_text("Calendar automation")
    record = FakeVectorRecord("v1", "c1", "d1", vector, "Calendar automation")
    await fake_vector_db.add(record)

    with pytest.raises(ValueError):
        await fake_vector_db.add(record)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_batch_indexing_counts_inserted_vectors(fake_vector_db, fake_embedding_generator):
    records = [
        FakeVectorRecord(f"v{i}", f"c{i}", "d1", await fake_embedding_generator.embed_text(f"text {i}"), f"text {i}")
        for i in range(3)
    ]

    inserted = await fake_vector_db.batch_add(records)

    assert inserted == 3
    assert len(fake_vector_db.records) == 3

