import re
from collections.abc import Callable
from typing import Any

from app.core.logger import log_event
from app.rag.models.document_models import ChunkingResult, DocumentChunk, RawDocument

TokenCounter = Callable[[str], int]


TOKEN_PATTERN = re.compile(r"\w+|[^\w\s]", re.UNICODE)


def estimate_token_count(text: str) -> int:
    """
    Dependency-light token estimator.

    R2 stays tokenizer-agnostic so a future embedding layer can inject the exact
    model tokenizer without changing the chunking contract.
    """

    value = str(text or "").strip()
    if not value:
        return 0
    return len(TOKEN_PATTERN.findall(value))


class TokenAwareChunker:
    """Create fixed-size token windows with configurable token overlap."""

    def __init__(
        self,
        *,
        chunk_size_tokens: int = 500,
        chunk_overlap_tokens: int = 75,
        token_counter: TokenCounter = estimate_token_count,
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

    async def chunk_document(self, document: RawDocument) -> ChunkingResult:
        chunks = self._chunk_text(document.content, document=document)
        total_tokens = sum(chunk.token_count for chunk in chunks)

        log_event(
            "rag_token_chunking_completed",
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

    def _chunk_text(
        self,
        text: str,
        *,
        document: RawDocument,
        base_metadata: dict[str, Any] | None = None,
    ) -> list[DocumentChunk]:
        spans = self._token_spans(text)
        if not spans:
            return []

        chunks: list[DocumentChunk] = []
        step = self.chunk_size_tokens - self.chunk_overlap_tokens
        start_token = 0

        while start_token < len(spans):
            end_token = min(start_token + self.chunk_size_tokens, len(spans))
            char_start = spans[start_token][0]
            char_end = spans[end_token - 1][1]
            chunk_text = text[char_start:char_end].strip()

            if chunk_text:
                token_count = self.token_counter(chunk_text)
                has_previous = start_token > 0
                has_next = end_token < len(spans)
                chunk_index = len(chunks)
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"{document.document_id}:token:{chunk_index:06d}",
                        document_id=document.document_id,
                        chunk_index=chunk_index,
                        content=chunk_text,
                        token_count=token_count,
                        character_count=len(chunk_text),
                        strategy="token",
                        overlap_previous_tokens=self.chunk_overlap_tokens if has_previous else 0,
                        overlap_next_tokens=self.chunk_overlap_tokens if has_next else 0,
                        document_metadata=document.metadata,
                        metadata={
                            "chunk_size_tokens": self.chunk_size_tokens,
                            "chunk_overlap_tokens": self.chunk_overlap_tokens,
                            "token_start": start_token,
                            "token_end": end_token,
                            "char_start": char_start,
                            "char_end": char_end,
                            **(base_metadata or {}),
                        },
                    )
                )

            if end_token >= len(spans):
                break
            start_token += step

        return chunks

    def _token_spans(self, text: str) -> list[tuple[int, int]]:
        return [(match.start(), match.end()) for match in TOKEN_PATTERN.finditer(text or "")]

