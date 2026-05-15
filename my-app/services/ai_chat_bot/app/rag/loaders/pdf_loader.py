import asyncio
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.core.logger import log_error, log_event
from app.rag.exceptions.ingestion_exceptions import CorruptedDocumentError, EmptyDocumentError
from app.rag.loaders.base_loader import BaseDocumentLoader
from app.rag.models.document_models import DocumentMetadata, DocumentSection, RawDocument


class PDFLoader(BaseDocumentLoader):
    loader_type = "pypdf"
    document_type = "pdf"
    supported_extensions = {".pdf"}

    async def load(self, file_path: str | Path) -> RawDocument:
        await self.validate_file(file_path)
        path = Path(file_path)

        try:
            page_texts = await asyncio.to_thread(self._extract_pages, path)
        except PdfReadError as exc:
            log_error("RAG PDF load failed", filename=path.name, error_type=type(exc).__name__)
            raise CorruptedDocumentError("pdf could not be read", details={"filename": path.name}) from exc
        except Exception as exc:
            log_error("RAG PDF load failed", filename=path.name, error_type=type(exc).__name__)
            raise CorruptedDocumentError("pdf extraction failed", details={"filename": path.name}) from exc

        sections = [
            DocumentSection(
                index=index,
                content=text,
                section_type="page",
                page_number=index + 1,
                metadata={"source": "pdf_page"},
            )
            for index, text in enumerate(page_texts)
            if text.strip()
        ]

        if not sections:
            raise EmptyDocumentError("pdf contains no extractable text", details={"filename": path.name})

        metadata = await self.extract_metadata(path)
        document = RawDocument(content="\n\n".join(section.content for section in sections), sections=sections, metadata=metadata)

        log_event(
            "rag_pdf_loaded",
            document_id=document.document_id,
            filename=metadata.filename,
            page_count=metadata.page_count,
        )
        return document

    async def extract_metadata(self, file_path: str | Path) -> DocumentMetadata:
        path = Path(file_path)
        page_count = await asyncio.to_thread(self._page_count, path)
        return await self.metadata_service.extract(
            path,
            loader_type=self.loader_type,
            document_type=self.document_type,
            page_count=page_count,
        )

    def _extract_pages(self, path: Path) -> list[str]:
        reader = PdfReader(str(path))
        pages: list[str] = []
        for page in reader.pages:
            extracted = page.extract_text() or ""
            pages.append(str(extracted))
        return pages

    def _page_count(self, path: Path) -> int:
        reader = PdfReader(str(path))
        return len(reader.pages)
