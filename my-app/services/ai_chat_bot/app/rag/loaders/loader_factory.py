from pathlib import Path

from app.core.logger import log_event
from app.rag.exceptions.ingestion_exceptions import UnsupportedFileTypeError
from app.rag.loaders.base_loader import BaseDocumentLoader
from app.rag.loaders.docx_loader import DOCXLoader
from app.rag.loaders.pdf_loader import PDFLoader
from app.rag.loaders.text_loader import TextLoader


class LoaderFactory:
    """Select the right document loader from a file extension."""

    def __init__(self, loaders: list[BaseDocumentLoader] | None = None) -> None:
        self.loaders = loaders or [PDFLoader(), DOCXLoader(), TextLoader()]

    def get_loader(self, file_path: str | Path) -> BaseDocumentLoader:
        path = Path(file_path)
        for loader in self.loaders:
            if loader.supports(path):
                log_event("rag_loader_selected", filename=path.name, loader_type=loader.loader_type)
                return loader

        raise UnsupportedFileTypeError(
            "no loader registered for extension",
            details={"extension": path.suffix.lower(), "filename": path.name},
        )
