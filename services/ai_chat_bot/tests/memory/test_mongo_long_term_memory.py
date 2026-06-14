import pytest


@pytest.mark.asyncio
@pytest.mark.unit
async def test_user_profile_storage_and_retrieval(fake_mongo):
    profiles = fake_mongo["profiles"]
    await profiles.insert_one({"user_id": "u1", "semantic_profile": "Prefers concise Hinglish replies"})

    profile = await profiles.find_one({"user_id": "u1"})

    assert profile is not None
    assert "Hinglish" in profile["semantic_profile"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_summary_persistence(fake_mongo):
    summaries = fake_mongo["summaries"]
    await summaries.insert_one({"user_id": "u1", "summary": "Asked about CRM automation"})

    summary = await summaries.find_one({"user_id": "u1"})

    assert summary["summary"] == "Asked about CRM automation"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_corrupted_memory_returns_none_instead_of_crashing(fake_mongo):
    profile = await fake_mongo["profiles"].find_one({"user_id": "missing"})

    assert profile is None

