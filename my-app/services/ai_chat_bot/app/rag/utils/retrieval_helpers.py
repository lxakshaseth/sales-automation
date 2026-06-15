from app.rag.models.ranking_models import RankedChunk


def deduplicate_ranked_chunks(chunks: list[RankedChunk]) -> list[RankedChunk]:
    seen: set[str] = set()
    unique: list[RankedChunk] = []
    for chunk in chunks:
        if chunk.chunk_id in seen:
            continue
        seen.add(chunk.chunk_id)
        unique.append(chunk)
    return [chunk.model_copy(update={"rank": index + 1}) for index, chunk in enumerate(unique)]


def cap_ranked_chunks(chunks: list[RankedChunk], top_k: int) -> list[RankedChunk]:
    return [chunk.model_copy(update={"rank": index + 1}) for index, chunk in enumerate(chunks[:top_k])]
