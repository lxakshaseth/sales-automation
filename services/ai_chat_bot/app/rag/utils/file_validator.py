import asyncio
from pathlib import Path

from app.rag.exceptions.ingestion_exceptions import EmptyDocumentError, FileValidationError, UnsupportedFileTypeError


class FileValidator:
    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}
    DEFAULT_MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024

    def __init__(self, max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES) -> None:
        self.max_file_size_bytes = max_file_size_bytes

    async def validate(self, file_path: str | Path) -> None:
        path = Path(file_path)
        await asyncio.to_thread(self._validate_sync, path)

    def _validate_sync(self, path: Path) -> None:
        if not path.exists() or not path.is_file():
            raise FileValidationError("file does not exist", details={"path": str(path)})

        extension = path.suffix.lower()
        if extension not in self.SUPPORTED_EXTENSIONS:
            raise UnsupportedFileTypeError(
                "unsupported file extension",
                details={"extension": extension, "supported_extensions": sorted(self.SUPPORTED_EXTENSIONS)},
            )

        file_size = path.stat().st_size
        if file_size <= 0:
            raise EmptyDocumentError("file is empty", details={"path": str(path)})

        if file_size > self.max_file_size_bytes:
            raise FileValidationError(
                "file exceeds max size",
                details={"file_size_bytes": file_size, "max_file_size_bytes": self.max_file_size_bytes},
            )

        # MIME and deep corruption checks are intentionally left as extension
        # points for upload gateways, S3 scanners, or OCR/document services.
