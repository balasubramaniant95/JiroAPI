import asyncio

from app import DatabaseManager
from bson.objectid import ObjectId
from config import config


class UserDBManager(DatabaseManager):
    """database manager for users route"""

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

    async def add_user(self, user: dict) -> dict:
        inserted = await self.collection.insert_one(user)
        if inserted.acknowledged:
            user = await self.collection.find_one({"_id": inserted.inserted_id})
            if user:
                return self._to_dict(user)
            else:
                raise RuntimeError(f"user added in database but could not be found: {inserted.inserted_id}")
        else:
            raise RuntimeError("failed to add user")

    async def update_user(self, id: str, data: dict) -> dict:
        updated = await self.collection.update_one({"_id": ObjectId(id)}, {"$set": data})
        if updated.acknowledged:
            user = await self.collection.find_one({"_id": ObjectId(id)})
            if user:
                return self._to_dict(user)
            else:
                raise RuntimeError(f"user updated in database but could not be found: {id}")
        else:
            raise RuntimeError(f"failed to update user")
