import asyncio
from typing import List

from app import DatabaseManager
from bson.objectid import ObjectId
from config import config


class TaskDBManager(DatabaseManager):
    """database manager for task route"""

    def __init__(self) -> None:
        DatabaseManager._client.get_io_loop = asyncio.get_running_loop

        self.db = DatabaseManager._client[config.MONGODB_DB]
        self.collection = self.db[config.MONGODB_COLLECTION_TASKS]

    def _to_dict(self, record) -> dict:
        record["_id"] = str(record["_id"])
        return record

    async def get_task_by_id(self, id: str) -> dict:
        task = await self.collection.find_one({"_id": ObjectId(id)})
        return self._to_dict(task) if task else {}

    async def get_tasks_by_created_by(self, created_by: str, skip: int, limit: int) -> List:
        tasks = [
            self._to_dict(task)
            async for task in self.collection.find({"created_by": created_by})
            .sort([("_id", 1)])
            .skip(skip)
            .limit(limit)
        ]
        return tasks if tasks else []

    async def add_task(self, task: dict) -> dict:
        inserted = await self.collection.insert_one(task)
        if inserted.acknowledged:
            task = await self.collection.find_one({"_id": inserted.inserted_id})
            if task:
                return self._to_dict(task)
            else:
                raise RuntimeError(f"task added in database but could not be found: {inserted.inserted_id}")
        else:
            raise RuntimeError("failed to add task")

    async def update_task(self, id: str, data: dict) -> dict:
        updated = await self.collection.update_one({"_id": ObjectId(id)}, {"$set": data})
        if updated.acknowledged:
            task = await self.collection.find_one({"_id": ObjectId(id)})
            if task:
                return self._to_dict(task)
            else:
                raise RuntimeError(f"task updated in database but could not be found: {id}")
        else:
            raise RuntimeError(f"failed to update task")

    async def replace_task(self, id: str, task: dict) -> dict:
        replaced = await self.collection.replace_one({"_id": ObjectId(id)}, task)
        if replaced.acknowledged:
            task = await self.collection.find_one({"_id": ObjectId(id)})
            if task:
                return self._to_dict(task)
            else:
                raise RuntimeError(f"task replaced in database but could not be found: {id}")
        else:
            raise RuntimeError(f"failed to replace task")

    async def delete_task(self, id: str) -> bool:
        deleted = await self.collection.delete_one({"_id": ObjectId(id)})
        if deleted.acknowledged:
            if deleted.deleted_count > 0:
                return True
            else:
                raise False
        else:
            raise RuntimeError(f"failed to delete task")
