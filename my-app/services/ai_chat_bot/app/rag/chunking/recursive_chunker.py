from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.logger import log_event
from app.rag.chunking.token_chunker import TokenCounter, estimate_token_count
from app.rag.models.document_models import ChunkingResult, DocumentChunk, RawDocument


class RecursiveDocumentChunker:
    """
    Recommended default chunker for R2.

    It uses LangChain's RecursiveCharacterTextSplitter with a token-aware length
    function, so paragraph and sentence boundaries are preferred while the final
    chunks target the configured token budget.
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", "? ", "! ", "; ", ", ", " ", ""]

    def __init__(
        self,
        *,
        chunk_size_tokens: int = 500,
        chunk_overlap_tokens: int = 75,
        token_counter: TokenCounter = estimate_token_count,
        separators: list[str] | None = None,
    ) -> None:
        if chunk_size_tokens <= 0:
            raise ValueError("chunk_size_tokens must be greater than zero")
        if chunk_overlap_tokens < 0:
            raise ValueError("chunk_overlap_tokens cannot be negative")
        if chunk_overlap_tokens >= chunk_size_tokens:
            raise ValueError("chunk_overlap_tokens must be smaller than chunk_size_tokens")

        self.chunk_size_tokens = chunk_size_tokens
        self.chunk_overlap_tokens = chunk_overlap_tokens
        self.token_counter = token_counter
        self.separators = separators or self.DEFAULT_SEPARATORS
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size_tokens,
            chunk_overlap=chunk_overlap_tokens,
            length_function=token_counter,
            separators=self.separators,
            keep_separator=True,
            is_separator_regex=False,
        )

    async def chunk_document(self, document: RawDocument) -> ChunkingResult:
        chunks = self._chunk_sections(document)
        total_tokens = sum(chunk.token_count for chunk in chunks)

        log_event(
            "rag_recursive_chunking_completed",
            document_id=document.document_id,
            filename=document.metadata.filename,
            chunk_count=len(chunks),
            total_tokens=total_tokens,
            chunk_size_tokens=self.chunk_size_tokens,
            chunk_overlap_tokens=self.chunk_overlap_tokens,
        )

        return ChunkingResult(
            success=True,
            chunks=chunks,
            chunk_count=len(chunks),
            total_tokens=total_tokens,
        )

    def _chunk_sections(self, document: RawDocument) -> list[DocumentChunk]:
        chunks: list[DocumentChunk] = []
        sections = document.sections or []

        if not sections and document.content.strip():
            split_texts = self.splitter.split_text(document.content)
            return self._build_chunks(document, split_texts, strategy_metadata={"source": "document_content"})

        for section in sections:
            if not section.content.strip():
                continue

            split_texts = self.splitter.split_text(section.content)
            section_chunks = self._build_chunks(
                document,
                split_texts,
                start_index=len(chunks),
                source_section_index=section.index,
                page_number=section.page_number,
                strategy_metadata={
                    "source": "document_section",
                    "section_type": section.section_type,
                    **section.metadata,
                },
            )
            chunks.extend(section_chunks)

        return chunks

    def _build_chunks(
        self,
        document: RawDocument,
        split_texts: list[str],
        *,
        start_index: int = 0,
        source_section_index: int | None = None,
        page_number: int | None = None,
        strategy_metadata: dict[str, Any] | None = None,
    ) -> list[DocumentChunk]:
        chunks: list[DocumentChunk] = []
        local_count = len([text for text in split_texts if text.strip()])

        for raw_text in split_texts:
            content = raw_text.strip()
            if not content:
                continue

            chunk_index = start_index + len(chunks)
            local_index = len(chunks)
            chunks.append(
                DocumentChunk(
                    chunk_id=f"{document.document_id}:recursive:{chunk_index:06d}",
                    document_id=document.document_id,
                    chunk_index=chunk_index,
                    content=content,
                    token_count=self.token_counter(content),
                    character_count=len(content),
                    strategy="recursive",
                    source_section_index=source_section_index,
                    page_number=page_number,
                    overlap_previous_tokens=self.chunk_overlap_tokens if local_index > 0 else 0,
                    overlap_next_tokens=self.chunk_overlap_tokens if local_index < local_count - 1 else 0,
                    document_metadata=document.metadata,
                    metadata={
                        "chunk_size_tokens": self.chunk_size_tokens,
                        "chunk_overlap_tokens": self.chunk_overlap_tokens,
                        **(strategy_metadata or {}),
                    },
                )
            )

        return chunks

