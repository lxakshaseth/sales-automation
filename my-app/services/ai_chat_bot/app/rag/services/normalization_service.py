import re
import unicodedata

from app.core.logger import log_event
from app.rag.models.document_models import DocumentSection, RawDocument


class NormalizationService:
    """Normalize extracted text without changing its semantic content."""

    CONTROL_CHARACTER_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
    HORIZONTAL_SPACE_PATTERN = re.compile(r"[ \t\f\v]+")
    EXCESSIVE_NEWLINES_PATTERN = re.compile(r"\n{3,}")

    async def normalize_document(self, document: RawDocument) -> RawDocument:
        normalized_sections = [
            section.model_copy(update={"content": self.normalize_text(section.content)})
            for section in document.sections
        ]
        normalized_content = self.normalize_text("\n\n".join(section.content for section in normalized_sections))

        normalized_document = document.model_copy(
            update={
                "content": normalized_content,
                "sections": normalized_sections,
                "normalized": True,
            }
        )

        log_event(
            "rag_normalization_completed",
            document_id=normalized_document.document_id,
            filename=normalized_document.metadata.filename,
            character_count=normalized_document.character_count,
        )
        return normalized_document

    def normalize_text(self, text: str) -> str:
        value = unicodedata.normalize("NFKC", str(text or ""))
        value = value.replace("\r\n", "\n").replace("\r", "\n")
        value = self.CONTROL_CHARACTER_PATTERN.sub("", value)
        lines = [self.HORIZONTAL_SPACE_PATTERN.sub(" ", line).strip() for line in value.split("\n")]
        value = "\n".join(lines)
        value = self.EXCESSIVE_NEWLINES_PATTERN.sub("\n\n", value)
        return value.strip()
