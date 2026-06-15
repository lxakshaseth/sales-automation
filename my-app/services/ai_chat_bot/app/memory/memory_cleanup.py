from app.core.logger import log_event
from app.models.optimization_models import MemoryCleanupResult
from app.models.summary_models import ConversationSummary


class MemoryCleanup:
    """Cleanup hooks for future Redis/Mongo memory retention policies."""

    async def cleanup_redundant_summaries(self, summaries: list[ConversationSummary], *, keep_latest: int = 20) -> MemoryCleanupResult:
        retained = summaries[:keep_latest]
        deleted_count = max(0, len(summaries) - len(retained))
        actions = ["identified_redundant_summaries"] if deleted_count else []
        log_event("memory_cleanup_completed", deleted_count=deleted_count, retained_count=len(retained))
        return MemoryCleanupResult(success=True, deleted_count=deleted_count, retained_count=len(retained), actions=actions)
