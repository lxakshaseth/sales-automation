from pathlib import Path

import pytest

from app.rag.models.document_models import IngestionResult
from app.rag.services.ingestion_service import IngestionService
from tests.fixtures.sample_data import make_document


class FakeLoader:
    def __init__(self, content: str | None = None, error: Exception | None = None) -> None:
        self.content = content
        self.error = error

    async def load(self, path: Path):
        if self.error:
            raise self.error
        return make_document(self.content if self.content is not None else path.read_text(encoding="utf-8"), filename=path.name)


class FakeLoaderFactory:
    def __init__(self, loader: FakeLoader) -> None:
        self.loader = loader

    def get_loader(self, path: Path) -> FakeLoader:
        if path.suffix not in {".txt", ".pdf", ".docx"}:
            raise ValueError("unsupported file")
        return self.loader


class FakeNormalizationService:
    async def normalize_document(self, document):
        document.normalized = True
        return document


@pytest.mark.asyncio
@pytest.mark.unit
async def test_txt_ingestion_preserves_unicode_and_metadata(tmp_text_file: Path, multilingual_text: str):
    service = IngestionService(
        loader_factory=FakeLoaderFactory(FakeLoader()),
        normalization_service=FakeNormalizationService(),
    )

    result = await service.ingest(tmp_text_file)

    assert isinstance(result, IngestionResult)
    assert result.success is True
    assert result.document is not None
    assert "नमस्ते" in result.document.content
    assert "pricing" in result.document.content
    assert result.document.metadata.filename == "sample.txt"
    assert result.document.normalized is True


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.parametrize("extension", [".pdf", ".docx"])
async def test_pdf_and_docx_loader_paths_are_supported(tmp_path: Path, extension: str):
    file_path = tmp_path / f"proposal{extension}"
    file_path.write_text("Enterprise CRM automation proposal", encoding="utf-8")
    service = IngestionService(
        loader_factory=FakeLoaderFactory(FakeLoader("Enterprise CRM automation proposal")),
        normalization_service=FakeNormalizationService(),
    )

    result = await service.ingest(file_path)

    assert result.success is True
    assert result.document is not None
    assert result.document.metadata.filename == file_path.name


@pytest.mark.asyncio
@pytest.mark.unit
async def test_corrupted_file_returns_structured_error(tmp_path: Path):
    file_path = tmp_path / "broken.pdf"
    file_path.write_bytes(b"%PDF-corrupted")
    service = IngestionService(
        loader_factory=FakeLoaderFactory(FakeLoader(error=RuntimeError("cannot parse"))),
        normalization_service=FakeNormalizationService(),
    )

    result = await service.ingest(file_path)

    assert result.success is False
    assert result.error is not None
    assert result.error["error_code"] == "ingestion_error"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_empty_file_is_ingested_without_crashing(tmp_path: Path):
    file_path = tmp_path / "empty.txt"
    file_path.write_text("", encoding="utf-8")
    service = IngestionService(
        loader_factory=FakeLoaderFactory(FakeLoader("")),
        normalization_service=FakeNormalizationService(),
    )

    result = await service.ingest(file_path)

    assert result.success is True
    assert result.document is not None
    assert result.document.character_count == 0
