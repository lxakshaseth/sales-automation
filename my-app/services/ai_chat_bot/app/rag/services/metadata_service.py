import mimetypes
from pathlib import Path
from typing import Any

from app.core.logger import log_event
from app.rag.models.document_models import DocumentMetadata
from app.rag.utils.file_helpers import calculate_checksum, get_file_size


class MetadataService:
    """Create consistent metadata for all document loaders."""

    async def extract(
        self,
        file_path: str | Path,
        *,
        loader_type: str,
        document_type: str,
        page_count: int | None = None,
        paragraph_count: int | None = None,
        extra: dict[str, Any] | None = None,
    ) -> DocumentMetadata:
        path = Path(file_path)
        file_size = await get_file_size(path)
        checksum = await calculate_checksum(path)
        mime_type, _ = mimetypes.guess_type(path.name)

        metadata = DocumentMetadata(
            filename=path.name,
            extension=path.suffix.lower(),
            file_size_bytes=file_size,
            source_type="local_file",
            loader_type=loader_type,
            document_type=document_type,
            checksum=checksum,
            language=None,
            page_count=page_count,
            paragraph_count=paragraph_count,
            mime_type=mime_type,
            source_path=str(path),
            extra=extra or {},
        )

        log_event(
            "rag_metadata_extracted",
            filename=metadata.filename,
            extension=metadata.extension,
            loader_type=metadata.loader_type,
            file_size_bytes=metadata.file_size_bytes,
            page_count=metadata.page_count,
            paragraph_count=metadata.paragraph_count,
        )
        return metadata
