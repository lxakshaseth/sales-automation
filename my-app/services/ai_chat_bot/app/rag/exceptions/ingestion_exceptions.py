from typing import Any


class IngestionError(RuntimeError):
    """Base class for production-safe ingestion failures."""

    error_code = "ingestion_error"
    safe_message = "Document ingestion failed."

    def __init__(self, message: str | None = None, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message or self.safe_message)
        self.details = details or {}

    def to_response(self) -> dict[str, Any]:
        return {
            "error_code": self.error_code,
            "message": self.safe_message,
            "details": self.details,
        }


class UnsupportedFileTypeError(IngestionError):
    error_code = "unsupported_file_type"
    safe_message = "Unsupported document type."


class EmptyDocumentError(IngestionError):
    error_code = "empty_document"
    safe_message = "Document is empty or contains no extractable text."


class FileValidationError(IngestionError):
    error_code = "file_validation_error"
    safe_message = "Document failed validation."


class CorruptedDocumentError(IngestionError):
    error_code = "corrupted_document"
    safe_message = "Document appears to be corrupted or unreadable."


class DocumentEncodingError(IngestionError):
    error_code = "document_encoding_error"
    safe_message = "Document encoding could not be decoded safely."

