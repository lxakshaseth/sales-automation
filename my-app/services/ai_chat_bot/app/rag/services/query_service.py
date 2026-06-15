from app.rag.retrieval.query_expansion import QueryExpansion
from app.rag.utils.query_helpers import normalize_query_text


class QueryService:
    """Preprocess and expand multilingual retrieval queries."""

    def __init__(self, *, expander: QueryExpansion | None = None) -> None:
        self.expander = expander or QueryExpansion()

    async def normalize(self, query: str) -> str:
        return normalize_query_text(query)

    async def expand(self, query: str, *, enabled: bool = True) -> list[str]:
        return await self.expander.expand(query, enabled=enabled)
