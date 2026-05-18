import re
from dataclasses import dataclass

from app.core.logger import log_event
from app.rag.chunking.recursive_chunker import RecursiveDocumentChunker
from app.rag.chunking.token_chunker import TokenCounter, estimate_token_count
from app.rag.models.document_models import ChunkingResult, DocumentChunk, DocumentSection, RawDocument


HEADING_PATTERN = re.compile(r"^(#{1,6}\s+.+|[A-Z][A-Z0-9\s\-:]{6,}|[0-9]+[.)]\s+.+)$")


@dataclass(frozen=True)
class SemanticBlock:
    title: str | None
    content: str
    section: DocumentSection | None = None


class SemanticDocumentChunker:
    """
    Structure-aware semantic chunker.

    This deliberately avoids embedding-based semantic splitting because R2 must
    not build embeddings yet. It preserves headings, paragraphs, pages, and DOCX
    sections, then delegates oversize blocks to the recursive chunker.
    """

    def __init__(
        self,
        *,
        chunk_size_tokens: int = 500,
        chunk_overlap_tokens: int = 75,
        token_counter: TokenCounter = estimate_token_count,
    ) -> None:
        self.chunk_size_tokens = chunk_size_tokens
        self.chunk_overlap_tokens = chunk_overlap_tokens
        self.token_counter = token_counter
        self.recursive_chunker = RecursiveDocumentChunker(
            chunk_size_tokens=chunk_size_tokens,
            chunk_overlap_tokens=chunk_overlap_tokens,
            token_counter=token_counter,
        )

    async def chunk_document(self, document: RawDocument) -> ChunkingResult:
        blocks = self._semantic_blocks(document)
        chunks: list[DocumentChunk] = []

        for block in blocks:
            if self.token_counter(block.content) <= self.chunk_size_tokens:
                chunk_index = len(chunks)
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"{document.document_id}:semantic:{chunk_index:06d}",
                        document_id=document.document_id,
                        chunk_index=chunk_index,
                        content=block.content.strip(),
                        token_count=self.token_counter(block.content),
                        character_count=len(block.content.strip()),
                        strategy="semantic",
                        source_section_index=block.section.index if block.section else None,
                        page_number=block.section.page_number if block.section else None,
                        document_metadata=document.metadata,
                        metadata={
                            "semantic_title": block.title,
                            "chunk_size_tokens": self.chunk_size_tokens,
                            "chunk_overlap_tokens": self.chunk_overlap_tokens,
                        },
                    )
                )
                continue

            synthetic = RawDocument(
                document_id=document.document_id,
                content=block.content,
                sections=[
                    DocumentSection(
                        index=block.section.index if block.section else 0,
                        content=block.content,
                        section_type=block.section.section_type if block.section else "semantic_block",
                        page_number=block.section.page_number if block.section else None,
                        metadata={"semantic_title": block.title},
                    )
                ],
                metadata=document.metadata,
                normalized=document.normalized,
            )
            recursive_result = await self.recursive_chunker.chunk_document(synthetic)
            for recursive_chunk in recursive_result.chunks:
                chunk_index = len(chunks)
                chunks.append(
                    recursive_chunk.model_copy(
                        update={
                            "chunk_id": f"{document.document_id}:semantic:{chunk_index:06d}",
                            "chunk_index": chunk_index,
                            "strategy": "semantic",
                            "metadata": {
                                **recursive_chunk.metadata,
                                "semantic_title": block.title,
                                "semantic_fallback": "recursive",
                            },
                        }
                    )
                )

        total_tokens = sum(chunk.token_count for chunk in chunks)
        log_event(
            "rag_semantic_chunking_completed",
            document_id=document.document_id,
            filename=document.metadata.filename,
            chunk_count=len(chunks),
            total_tokens=total_tokens,
            chunk_size_tokens=self.chunk_size_tokens,
        )
        return ChunkingResult(success=True, chunks=chunks, chunk_count=len(chunks), total_tokens=total_tokens)

    def _semantic_blocks(self, document: RawDocument) -> list[SemanticBlock]:
        blocks: list[SemanticBlock] = []

        if document.sections:
            for section in document.sections:
                blocks.extend(self._blocks_from_text(section.content, section=section))
        else:
            blocks.extend(self._blocks_from_text(document.content, section=None))

        return [block for block in blocks if block.content.strip()]

    def _blocks_from_text(self, text: str, *, section: DocumentSection | None) -> list[SemanticBlock]:
        paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n", text or "") if paragraph.strip()]
        if not paragraphs:
            return []

        blocks: list[SemanticBlock] = []
        current_title: str | None = None
        current_parts: list[str] = []

        for paragraph in paragraphs:
            first_line = paragraph.splitlines()[0].strip()
            is_heading = bool(HEADING_PATTERN.match(first_line)) and self.token_counter(paragraph) <= 30

            if is_heading:
                if current_parts:
                    blocks.append(SemanticBlock(title=current_title, content="\n\n".join(current_parts), section=section))
                    current_parts = []
                current_title = first_line
                current_parts.append(paragraph)
                continue

            current_parts.append(paragraph)

        if current_parts:
            blocks.append(SemanticBlock(title=current_title, content="\n\n".join(current_parts), section=section))

        return blocks
