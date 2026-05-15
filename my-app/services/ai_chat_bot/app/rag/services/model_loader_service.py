import asyncio
from typing import Any

from app.core.logger import log_error, log_event
from app.rag.exceptions.embedding_exceptions import EmbeddingModelLoadError
from app.rag.models.embedding_models import DEFAULT_EMBEDDING_MODEL, EmbeddingConfig


class ModelLoaderService:
    """Lazy singleton loader for local sentence-transformer embedding models."""

    _models: dict[str, Any] = {}
    _locks: dict[str, asyncio.Lock] = {}
    _global_lock = asyncio.Lock()

    async def get_embedding_model(self, config: EmbeddingConfig | None = None) -> Any:
        resolved_config = config or EmbeddingConfig()
        model_name = resolved_config.model_name or DEFAULT_EMBEDDING_MODEL

        if model_name in self._models:
            return self._models[model_name]

        async with self._global_lock:
            lock = self._locks.setdefault(model_name, asyncio.Lock())

        async with lock:
            if model_name in self._models:
                return self._models[model_name]

            try:
                log_event("rag_embedding_model_loading", model_name=model_name, device=resolved_config.device)
                model = await asyncio.to_thread(self._load_model_sync, resolved_config)
                self._models[model_name] = model
                log_event("rag_embedding_model_loaded", model_name=model_name)
                return model
            except Exception as exc:
                log_error("RAG embedding model loading failed", model_name=model_name, error_type=type(exc).__name__)
                raise EmbeddingModelLoadError("failed to load embedding model", details={"model_name": model_name}) from exc

    def _load_model_sync(self, config: EmbeddingConfig) -> Any:
        try:
            from sentence_transformers import SentenceTransformer
        except Exception as exc:
            raise EmbeddingModelLoadError(
                "sentence-transformers is not installed",
                details={"package": "sentence-transformers"},
            ) from exc

        kwargs = dict(config.model_kwargs)
        if config.device:
            kwargs["device"] = config.device
        return SentenceTransformer(config.model_name, **kwargs)

    async def unload_model(self, model_name: str) -> None:
        async with self._global_lock:
            self._models.pop(model_name, None)

