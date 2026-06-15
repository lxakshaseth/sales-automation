import asyncio
from pathlib import Path

import pytest

from app.models.context_models import TokenBudget
from tests.fixtures.sample_data import make_chat_message, make_document, make_ranked_chunk
from tests.mocks.fake_embeddings import FakeEmbeddingGenerator
from tests.mocks.fake_mongo import FakeMongoDatabase
from tests.mocks.fake_redis import FakeRedis
from tests.mocks.fake_vector_db import FakeVectorDB, FakeVectorRecord


@pytest.fixture(scope="session")
def event_loop_policy():
    return asyncio.WindowsSelectorEventLoopPolicy() if hasattr(asyncio, "WindowsSelectorEventLoopPolicy") else asyncio.DefaultEventLoopPolicy()


@pytest.fixture
def fake_redis() -> FakeRedis:
    return FakeRedis()


@pytest.fixture
def fake_mongo() -> FakeMongoDatabase:
    return FakeMongoDatabase()


@pytest.fixture
def fake_embedding_generator() -> FakeEmbeddingGenerator:
    return FakeEmbeddingGenerator(dimension=8)


@pytest.fixture
def fake_vector_db() -> FakeVectorDB:
    return FakeVectorDB()


@pytest.fixture
def multilingual_text() -> str:
    return "Hello Akshat, नमस्ते! WhatsApp automation ka pricing aur CRM follow-up discuss karna hai."


@pytest.fixture
def raw_document(multilingual_text: str):
    return make_document(multilingual_text)


@pytest.fixture
def retrieved_chunks():
    return [
        make_ranked_chunk("Akshat asked for WhatsApp automation pricing and CRM integration.", chunk_id="c1", score=0.93),
        make_ranked_chunk("Office lunch menu is unrelated to enterprise automation.", chunk_id="c2", score=0.12, rank=2),
    ]


@pytest.fixture
def chat_messages():
    return [
        make_chat_message("Please keep the follow-up concise.", index=1),
        make_chat_message("Sure, I will keep it professional.", role="assistant", index=2),
    ]


@pytest.fixture
def small_token_budget() -> TokenBudget:
    return TokenBudget(model_name="gpt-4o-mini", max_context_tokens=1200, reserved_response_tokens=200, system_prompt_tokens=200)


@pytest.fixture
async def seeded_vector_db(fake_vector_db: FakeVectorDB, fake_embedding_generator: FakeEmbeddingGenerator):
    docs = [
        ("v1", "c1", "doc-sales", "WhatsApp CRM pricing follow-up automation"),
        ("v2", "c2", "doc-calendar", "Calendar booking reminders and meeting slots"),
        ("v3", "c3", "doc-noise", "Completely unrelated cafeteria schedule"),
    ]
    for vector_id, chunk_id, document_id, content in docs:
        await fake_vector_db.add(
            FakeVectorRecord(
                vector_id=vector_id,
                chunk_id=chunk_id,
                document_id=document_id,
                vector=await fake_embedding_generator.embed_text(content),
                content=content,
            )
        )
    return fake_vector_db


@pytest.fixture
def tmp_text_file(tmp_path: Path, multilingual_text: str) -> Path:
    path = tmp_path / "sample.txt"
    path.write_text(multilingual_text, encoding="utf-8")
    return path
