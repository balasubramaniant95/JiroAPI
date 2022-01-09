from abc import ABC

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ServerSelectionTimeoutError


class DatabaseManager(ABC):
    """base class for database manager"""

    _initialized = False
    _client = None

    @classmethod
    def init(cls, client: AsyncIOMotorClient):
        if cls._initialized:
            return None

        cls._initialized = True
        cls._client = client

    @staticmethod
    def ping() -> bool:
        try:
            _ = DatabaseManager._client.address
            return True
        except ServerSelectionTimeoutError:
            return False
