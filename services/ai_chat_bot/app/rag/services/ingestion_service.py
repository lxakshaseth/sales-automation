from pathlib import Path

from app.core.logger import log_error, log_event
from app.rag.exceptions.ingestion_exceptions import IngestionError
from app.rag.loaders.loader_factory import LoaderFactory
from app.rag.models.document_models import IngestionResult
from app.rag.services.normalization_service import NormalizationService


class IngestionService:
    """Orchestrate Layer R1 document ingestion for internal AI services."""

    def __init__(
        self,
        *,
        loader_factory: LoaderFactory | None = None,
        normalization_service: NormalizationService | None = None,
    ) -> None:
        self.loader_factory = loader_factory or LoaderFactory()
        self.normalization_service = normalization_service or NormalizationService()

    async def ingest(self, file_path: str | Path) -> IngestionResult:
        path = Path(file_path)
        log_event("rag_ingestion_started", filename=path.name, source_path=str(path))

        try:
            loader = self.loader_factory.get_loader(path)
            raw_document = await loader.load(path)
            normalized_document = await self.normalization_service.normalize_document(raw_document)

            log_event(
                "rag_ingestion_success",
                document_id=normalized_document.document_id,
                filename=normalized_document.metadata.filename,
                loader_type=normalized_document.metadata.loader_type,
                character_count=normalized_document.character_count,
                section_count=len(normalized_document.sections),
            )
            return IngestionResult(success=True, document=normalized_document)
        except IngestionError as exc:
            log_error(
                "RAG ingestion failed",
                filename=path.name,
                error_code=exc.error_code,
                error_type=type(exc).__name__,
            )
            return IngestionResult(success=False, error=exc.to_response())
        except Exception as exc:
            log_error("Unexpected RAG ingestion failure", filename=path.name, error_type=type(exc).__name__, exc_info=True)
            error = IngestionError(details={"filename": path.name, "error_type": type(exc).__name__})
            return IngestionResult(success=False, error=error.to_response())
