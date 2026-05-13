import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from bson import ObjectId
from pymongo.errors import PyMongoError

from app.tools import mongo_tool
from app.tools.mongo_tool import (
    CONVERSATIONS_COLLECTION,
    LEADS_COLLECTION,
    SUMMARIES_COLLECTION,
    MongoStoreError,
    get_chat_history,
    save_chat,
    save_lead,
    save_summary,
)


class MongoToolTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        mongo_tool._indexes_created = False
        self.collections = {
            CONVERSATIONS_COLLECTION: MagicMock(),
            SUMMARIES_COLLECTION: MagicMock(),
            LEADS_COLLECTION: MagicMock(),
        }
        self.collection_patch = patch.object(
            mongo_tool,
            "_collection",
            side_effect=lambda name: self.collections[name],
        )
        self.collection_patch.start()

    def tearDown(self):
        self.collection_patch.stop()
        mongo_tool._indexes_created = False

    async def test_save_chat_stores_conversation_document(self):
        inserted_id = ObjectId()
        self.collections[CONVERSATIONS_COLLECTION].insert_one.return_value.inserted_id = inserted_id

        result = await save_chat(
            user_id="user-123",
            messages=[{"role": "user", "content": "Hello"}],
            intents=["greeting"],
            lead_status="new",
        )

        self.assertEqual(result["_id"], str(inserted_id))
        self.assertEqual(result["user_id"], "user-123")
        self.assertEqual(result["messages"], [{"role": "user", "content": "Hello"}])
        self.assertEqual(result["intents"], ["greeting"])
        self.assertEqual(result["lead_status"], "new")
        self.collections[CONVERSATIONS_COLLECTION].insert_one.assert_called_once()

    async def test_get_chat_history_limits_and_serializes_results(self):
        document_id = ObjectId()
        cursor = MagicMock()
        cursor.sort.return_value = cursor
        cursor.limit.return_value = [{"_id": document_id, "user_id": "user-123", "created_at": datetime(2026, 5, 7)}]
        self.collections[CONVERSATIONS_COLLECTION].find.return_value = cursor

        result = await get_chat_history("user-123", limit=500)

        self.assertEqual(result[0]["_id"], str(document_id))
        cursor.limit.assert_called_once_with(200)

    async def test_save_summary_stores_summary_document(self):
        inserted_id = ObjectId()
        self.collections[SUMMARIES_COLLECTION].insert_one.return_value.inserted_id = inserted_id

        result = await save_summary("user-123", "Short summary", intents=["follow_up"])

        self.assertEqual(result["_id"], str(inserted_id))
        self.assertEqual(result["summary"], "Short summary")
        self.assertEqual(result["intents"], ["follow_up"])

    async def test_save_lead_upserts_user_lead_state(self):
        lead_id = ObjectId()
        self.collections[LEADS_COLLECTION].find_one_and_update.return_value = {
            "_id": lead_id,
            "user_id": "user-123",
            "lead_status": "qualified",
        }

        result = await save_lead("user-123", "qualified", {"email": "user@example.com"})

        self.assertEqual(result["_id"], str(lead_id))
        self.assertEqual(result["lead_status"], "qualified")
        self.collections[LEADS_COLLECTION].find_one_and_update.assert_called_once()

    async def test_pymongo_errors_are_wrapped(self):
        self.collections[CONVERSATIONS_COLLECTION].insert_one.side_effect = PyMongoError("write failed")

        with patch.object(mongo_tool.logger, "exception"), self.assertRaises(MongoStoreError):
            await save_chat("user-123", messages=[])


if __name__ == "__main__":
    unittest.main()
