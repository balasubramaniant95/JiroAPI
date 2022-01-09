import aioredis
import motor.motor_asyncio
from config import config
from db.cache import CacheManager
from db.db import DatabaseManager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# init app
app = FastAPI(
    title="TaskAPI",
    description="API backend for Jirotion App",
    version="0.1.0",
    redoc_url=None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# init database & cache
DatabaseManager.init(
    client=motor.motor_asyncio.AsyncIOMotorClient(config.MONGODB_URI, authSource="admin", serverSelectionTimeoutMS=3000)
)
CacheManager.init(
    client=aioredis.from_url(config.REDIS_URI, encoding="utf-8", decode_responses=True),
    default_timeout=config.CACHE_TIMEOUT,
    crypto_key=config.REDIS_CRYPTO_KEY,
)


# load api routes
from api.health import router as health_router
from api.login.routes import router as login_router
from api.tasks.routes import router as task_router
from api.users.routes import router as user_router

app.include_router(health_router, tags=["health"], prefix="/health")
app.include_router(user_router, tags=["users"], prefix="/users")
app.include_router(login_router, tags=["login"], prefix="/login")
app.include_router(task_router, tags=["tasks"], prefix="/tasks")
