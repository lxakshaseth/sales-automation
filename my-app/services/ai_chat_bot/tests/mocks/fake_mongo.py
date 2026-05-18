from copy import deepcopy
from typing import Any


class FakeMongoCollection:
    """Tiny async MongoDB collection fake for memory persistence tests."""

    def __init__(self) -> None:
        self.documents: list[dict[str, Any]] = []

    async def insert_one(self, document: dict[str, Any]):
        stored = deepcopy(document)
        stored.setdefault("_id", str(len(self.documents) + 1))
        self.documents.append(stored)
        return type("InsertOneResult", (), {"inserted_id": stored["_id"]})()

    async def find_one(self, query: dict[str, Any]) -> dict[str, Any] | None:
        for document in self.documents:
            if all(document.get(key) == value for key, value in query.items()):
                return deepcopy(document)
        return None

    async def update_one(self, query: dict[str, Any], update: dict[str, Any], upsert: bool = False):
        document = await self.find_one(query)
        if document is None and upsert:
            document = dict(query)
            self.documents.append(document)
        if document is not None:
            document.update(update.get("$set", {}))
        return type("UpdateResult", (), {"matched_count": int(document is not None), "modified_count": int(document is not None)})()


class FakeMongoDatabase(dict[str, FakeMongoCollection]):
    def __getitem__(self, name: str) -> FakeMongoCollection:
        if name not in self:
            self[name] = FakeMongoCollection()
        return super().__getitem__(name)

