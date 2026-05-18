import asyncio
from pathlib import Path

from app.core.logger import log_error, log_event
from app.rag.exceptions.ingestion_exceptions import DocumentEncodingError, EmptyDocumentError
from app.rag.loaders.base_loader import BaseDocumentLoader
from app.rag.models.document_models import DocumentMetadata, DocumentSection, RawDocument
from app.rag.utils.encoding_detector import EncodingDetector


class TextLoader(BaseDocumentLoader):
    loader_type = "plain-text"
    document_type = "txt"
    supported_extensions = {".txt"}

    def __init__(self, *, encoding_detector: EncodingDetector | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.encoding_detector = encoding_detector or EncodingDetector()

    async def load(self, file_path: str | Path) -> RawDocument:
        await self.validate_file(file_path)
        path = Path(file_path)
        encoding = await self.encoding_detector.detect(path)

        try:
            content = await asyncio.to_thread(path.read_text, encoding=encoding, errors="replace")
        except UnicodeError as exc:
            log_error("RAG text load failed", filename=path.name, encoding=encoding, error_type=type(exc).__name__)
            raise DocumentEncodingError("text file could not be decoded", details={"filename": path.name}) from exc

        if not content.strip():
            raise EmptyDocumentError("text file contains no content", details={"filename": path.name})

        sections = [DocumentSection(index=0, content=content, section_type="text", metadata={"encoding": encoding})]
        metadata = await self.extract_metadata(path)
        metadata.extra["encoding"] = encoding
        document = RawDocument(content=content, sections=sections, metadata=metadata)

        log_event(
            "rag_text_loaded",
            document_id=document.document_id,
            filename=metadata.filename,
            encoding=encoding,
            character_count=document.character_count,
        )
        return document

    async def extract_metadata(self, file_path: str | Path) -> DocumentMetadata:
        path = Path(file_path)
        return await self.metadata_service.extract(
            path,
            loader_type=self.loader_type,
            document_type=self.document_type,
        )
