import asyncio

from app import DatabaseManager
from bson.objectid import ObjectId
from config import config


class AuthDBManager(DatabaseManager):
    """database manager for login route"""

    def __init__(self) -> None:
        DatabaseManager._client.get_io_loop = asyncio.get_running_loop

        self.db = DatabaseManager._client[config.MONGODB_DB]
        self.collection = self.db[config.MONGODB_COLLECTION_USERS]

    def _to_dict(self, record: dict) -> dict:
        record["_id"] = str(record["_id"])
        return record

    async def get_user_by_id(self, id: str) -> dict:
        user = await self.collection.find_one({"_id": ObjectId(id)})
        return self._to_dict(user) if user else {}

    async def get_user_by_email(self, email: str) -> dict:
        user = await self.collection.find_one({"email": email})
        return self._to_dict(user) if user else {}
