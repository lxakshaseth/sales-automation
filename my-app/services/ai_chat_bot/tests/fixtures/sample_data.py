from app.models.message_models import ChatMessage
from app.rag.models.document_models import DocumentMetadata, DocumentSection, RawDocument
from app.rag.models.ranking_models import RankedChunk


def make_document(content: str, *, filename: str = "sample.txt") -> RawDocument:
    metadata = DocumentMetadata(
        filename=filename,
        extension=".txt",
        file_size_bytes=len(content.encode("utf-8")),
        loader_type="fake_txt_loader",
        document_type="txt",
        language="hi-en",
    )
    return RawDocument(
        content=content,
        sections=[DocumentSection(index=0, content=content, section_type="body")],
        metadata=metadata,
        normalized=True,
    )


def make_ranked_chunk(content: str, *, chunk_id: str = "chunk-1", score: float = 0.9, rank: int = 1) -> RankedChunk:
    return RankedChunk(
        chunk_id=chunk_id,
        document_id="doc-1",
        vector_id=f"vec-{chunk_id}",
        rank=rank,
        similarity_score=score,
        final_score=score,
        source_filename="knowledge.txt",
        content=content,
    )


def make_chat_message(text: str, *, role: str = "user", index: int = 1) -> ChatMessage:
    return ChatMessage(
        message_id=f"msg-{index}",
        session_id="session-1",
        user_id="user-1",
        role=role,  # type: ignore[arg-type]
        message_text=text,
    )

