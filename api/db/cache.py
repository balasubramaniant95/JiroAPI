import json
from typing import Any

from aioredis import Redis
from aioredis.exceptions import ConnectionError
from cryptography.fernet import Fernet


class CacheManager:
    """base class for cache manager"""

    _initialized = False
    _client = None
    _default_timeout = None
    _cipher = None

    @classmethod
    def init(cls, client: Redis, default_timeout: int, crypto_key: str):
        if cls._initialized:
            return None

        cls._initialized = True
        cls._client = client
        cls._default_timeout = default_timeout
        cls._cipher = Fernet(crypto_key.encode("utf-8"))

    @staticmethod
    async def ping() -> bool:
        try:
            return await CacheManager._client.ping()
        except ConnectionError:
            return False

    @staticmethod
    async def store(key: str, value: str, timeout: int = None) -> bool:
        if timeout is None:
            timeout = CacheManager._default_timeout
        try:
            return await CacheManager._client.setex(
                key,
                timeout,
                CacheManager._cipher.encrypt(json.dumps(value).encode("utf-8")),
            )
        except ConnectionError:
            return False

    @staticmethod
    async def fetch(key: str) -> Any:
        try:
            value = await CacheManager._client.get(key)
            if not value:
                return None

            return json.loads(CacheManager._cipher.decrypt(value.encode("utf-8")))
        except ConnectionError:
            return None

    @staticmethod
    async def delete(key: str, scan: bool = False) -> bool:
        deleted = 0
        try:
            if scan:
                async for k in CacheManager._client.scan_iter(match=key):
                    deleted += await CacheManager._client.delete(k)
            else:
                deleted += await CacheManager._client.delete(key)

            return True if deleted else False
        except ConnectionError:
            return False
