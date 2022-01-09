from pathlib import Path
from typing import Optional

from pydantic import BaseSettings
from pydantic.fields import Field


class Config(BaseSettings):
    """base class used to configure the app"""

    CACHE_TIMEOUT: int = Field(300, env="CACHE_TIMEOUT")
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_TIMEOUT: int = Field(30, env="ACCESS_TOKEN_EXPIRE_TIMEOUT")
    PORT: int = Field(8000, env="PORT")

    REDIS_DB: int = Field(0, env="REDIS_DB")
    REDIS_CRYPTO_KEY: str = Field(..., env="REDIS_CRYPTO_KEY")

    REDIS_PASSWD: str = Field(..., env="REDIS_PASSWD")
    REDIS_HOST: str = Field("localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(6379, env="REDIS_PORT")
    REDIS_URI: Optional[str]

    MONGODB_DB: str = Field("jiro_db", env="MONGODB_DB")
    MONGODB_COLLECTION_TASKS: str = Field("tasks", env="MONGODB_COLLECTION_TASKS")
    MONGODB_COLLECTION_USERS: str = Field("users", env="MONGODB_COLLECTION_USERS")

    MONGODB_USER: str = Field(..., env="MONGODB_USER")
    MONGODB_PASSWD: str = Field(..., env="MONGODB_PASSWD")
    MONGODB_HOST: str = Field("localhost", env="MONGODB_HOST")
    MONGODB_PORT: int = Field(27017, env="MONGODB_PORT")
    MONGODB_URI: Optional[str]

    class Config:
        case_sensitive = True
        env_file = Path(__file__).parent.joinpath(".env")
        env_file_encoding = "utf-8"


config = Config()
config.MONGODB_URI = (
    f"mongodb://{config.MONGODB_USER}:{config.MONGODB_PASSWD}@{config.MONGODB_HOST}:{config.MONGODB_PORT}/"
)
config.REDIS_URI = f"redis://:{config.REDIS_PASSWD}@{config.REDIS_HOST}:{config.REDIS_PORT}/{config.REDIS_DB}"
