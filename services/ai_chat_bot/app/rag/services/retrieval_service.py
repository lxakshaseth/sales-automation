from app.rag.models.retrieval_models import RetrievalRequest, RetrievalResult
from app.rag.retrieval.retrieval_manager import RetrievalManager


class RetrievalService:
    """Internal semantic retrieval interface for future AI context builders."""

    def __init__(self, *, manager: RetrievalManager | None = None) -> None:
        self.manager = manager or RetrievalManager()

    async def retrieve(self, request: RetrievalRequest) -> RetrievalResult:
        return await self.manager.retrieve(request)
