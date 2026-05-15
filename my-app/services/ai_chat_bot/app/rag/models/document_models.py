from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


DocumentType = Literal["pdf", "docx", "txt"]
SourceType = Literal["local_file", "upload", "s3", "url", "unknown"]
ChunkingStrategy = Literal["recursive", "semantic", "token"]


class DocumentSection(BaseModel):
    """A stable unit of extracted source content before chunking exists."""

    index: int = Field(ge=0)
    content: str = ""
    section_type: str = Field(default="body", max_length=80)
    page_number: int | None = Field(default=None, ge=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("content")
    @classmethod
    def clean_content(cls, value: str) -> str:
        return str(value or "")


class DocumentMetadata(BaseModel):
    filename: str
    extension: str
    file_size_bytes: int = Field(default=0, ge=0)
    source_type: SourceType = "local_file"
    loader_type: str = Field(default="", max_length=120)
    document_type: DocumentType
    upload_timestamp: datetime = Field(default_factory=utc_now)
    checksum: str | None = None
    language: str | None = None
    page_count: int | None = Field(default=None, ge=0)
    paragraph_count: int | None = Field(default=None, ge=0)
    mime_type: str | None = None
    source_path: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)

    @field_validator("extension")
    @classmethod
    def normalize_extension(cls, value: str) -> str:
        normalized = str(value or "").lower().strip()
        return normalized if normalized.startswith(".") else f".{normalized}"


class RawDocument(BaseModel):
    document_id: str = Field(default_factory=lambda: str(uuid4()))
    content: str = ""
    sections: list[DocumentSection] = Field(default_factory=list)
    metadata: DocumentMetadata
    normalized: bool = False
    created_at: datetime = Field(default_factory=utc_now)

    @property
    def character_count(self) -> int:
        return len(self.content)


class IngestionResult(BaseModel):
    success: bool
    document: RawDocument | None = None
    error: dict[str, Any] | None = None
    warnings: list[str] = Field(default_factory=list)
    ingested_at: datetime = Field(default_factory=utc_now)


class DocumentChunk(BaseModel):
    """AI-ready text unit produced by Layer R2 before embeddings exist."""

    chunk_id: str
    document_id: str
    chunk_index: int = Field(ge=0)
    content: str
    token_count: int = Field(default=0, ge=0)
    character_count: int = Field(default=0, ge=0)
    strategy: ChunkingStrategy
    source_section_index: int | None = Field(default=None, ge=0)
    page_number: int | None = Field(default=None, ge=1)
    overlap_previous_tokens: int = Field(default=0, ge=0)
    overlap_next_tokens: int = Field(default=0, ge=0)
    document_metadata: DocumentMetadata
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)

    @field_validator("content")
    @classmethod
    def clean_chunk_content(cls, value: str) -> str:
        return str(value or "").strip()


class ChunkingResult(BaseModel):
    success: bool
    chunks: list[DocumentChunk] = Field(default_factory=list)
    error: dict[str, Any] | None = None
    warnings: list[str] = Field(default_factory=list)
    chunk_count: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    chunked_at: datetime = Field(default_factory=utc_now)
