from abc import ABC, abstractmethod
from pathlib import Path

from app.rag.models.document_models import DocumentMetadata, RawDocument
from app.rag.services.metadata_service import MetadataService
from app.rag.utils.file_validator import FileValidator


class BaseDocumentLoader(ABC):
    """Abstract async interface for RAG document loaders."""

    loader_type: str
    document_type: str
    supported_extensions: set[str]

    def __init__(
        self,
        *,
        metadata_service: MetadataService | None = None,
        file_validator: FileValidator | None = None,
    ) -> None:
        self.metadata_service = metadata_service or MetadataService()
        self.file_validator = file_validator or FileValidator()

    async def validate_file(self, file_path: str | Path) -> None:
        await self.file_validator.validate(file_path)

    @abstractmethod
    async def load(self, file_path: str | Path) -> RawDocument:
        """Load a source file into a standardized RawDocument."""

    @abstractmethod
    async def extract_metadata(self, file_path: str | Path) -> DocumentMetadata:
        """Extract source-specific metadata."""

    def supports(self, file_path: str | Path) -> bool:
        return Path(file_path).suffix.lower() in self.supported_extensions
