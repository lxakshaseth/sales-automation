from app.core.logger import log_event
from app.intelligence.optimization import TokenOptimizer
from app.intelligence.orchestration.exceptions import ContextBuildError
from app.intelligence.orchestration.models import ContextBundle, OrchestrationRequest


class ContextManager:
    """Builds and validates priority-ordered context for AI orchestration."""

    def __init__(self, token_optimizer: TokenOptimizer | None = None) -> None:
        self.token_optimizer = token_optimizer or TokenOptimizer()

    async def build_context(self, request: OrchestrationRequest) -> ContextBundle:
        try:
            bundle = ContextBundle(
                system_prompt=request.system_prompt,
                current_query=request.user_query,
                tool_results=request.tool_outputs,
                retrieved_chunks=request.retrieved_chunks,
                memory_summary=self._memory_summary(request.conversation_history),
                chat_history=request.conversation_history,
                crm_context=request.crm_context,
                user_preferences={"language": request.preferred_language, "persona": request.persona},
                metadata=request.metadata,
            )
            bundle = self.merge_context(bundle)
            bundle = self.prioritize_context(bundle)
            self.validate_context(bundle)
            log_event("orchestration_context_built", retrieved_count=len(bundle.retrieved_chunks), history_count=len(bundle.chat_history))
            return bundle
        except Exception as exc:
            raise ContextBuildError("failed to build orchestration context") from exc

    def merge_context(self, context: ContextBundle) -> ContextBundle:
        return context

    def prioritize_context(self, context: ContextBundle) -> ContextBundle:
        context.retrieved_chunks.sort(key=lambda chunk: float(chunk.get("score", chunk.get("relevance", 0.0)) or 0.0), reverse=True)
        return context

    async def compress_context(self, context: ContextBundle):
        return await self.token_optimizer.optimize_context(
            {
                "system_prompt": context.system_prompt,
                "user_query": context.current_query,
                "rag_context": context.retrieved_chunks,
                "history": context.chat_history,
                "tool_outputs": context.tool_results,
                "metadata": context.metadata,
            }
        )

    def validate_context(self, context: ContextBundle) -> bool:
        if not context.current_query.strip():
            raise ContextBuildError("current query is required")
        return True

    def _memory_summary(self, history: list[dict]) -> str:
        important = []
        for message in history[-5:]:
            content = str(message.get("content") or message.get("message") or "")
            if content:
                important.append(content)
        return " | ".join(important)
