import pytest

BENCHMARK_QUERIES = [
    {
        "query": "WhatsApp CRM pricing follow-up",
        "relevant_document_ids": {"doc-sales"},
    },
    {
        "query": "calendar meeting reminder slots",
        "relevant_document_ids": {"doc-calendar"},
    },
]


def precision_at_k(results: list[dict], relevant: set[str], k: int) -> float:
    top = results[:k]
    if not top:
        return 0.0
    hits = sum(1 for result in top if result["document_id"] in relevant)
    return hits / len(top)


def recall_at_k(results: list[dict], relevant: set[str], k: int) -> float:
    if not relevant:
        return 1.0
    hits = {result["document_id"] for result in results[:k]} & relevant
    return len(hits) / len(relevant)


@pytest.mark.asyncio
@pytest.mark.performance
async def test_enterprise_retrieval_precision_and_recall(seeded_vector_db, fake_embedding_generator):
    scores: list[tuple[float, float]] = []
    for item in BENCHMARK_QUERIES:
        query_vector = await fake_embedding_generator.embed_text(item["query"])
        results = await seeded_vector_db.search(query_vector, top_k=2)
        scores.append(
            (
                precision_at_k(results, item["relevant_document_ids"], 2),
                recall_at_k(results, item["relevant_document_ids"], 2),
            )
        )

    average_precision = sum(score[0] for score in scores) / len(scores)
    average_recall = sum(score[1] for score in scores) / len(scores)
    assert average_precision >= 0.5
    assert average_recall >= 0.5

