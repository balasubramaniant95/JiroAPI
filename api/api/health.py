from app import CacheManager, DatabaseManager
from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def get_health():
    """show app health"""

    redis_health = await CacheManager.ping()
    mongodb_health = DatabaseManager.ping()

    status = "RED"
    if mongodb_health:
        status = "GREEN" if redis_health else "YELLOW"

    message = "Api is live & Kicking!" if (redis_health and mongodb_health) else "Database or Cache is DOWN (or both)"

    return {
        "status": status,
        "message": message,
        "redis": "Up" if redis_health else "Down",
        "mongodb": "Up" if mongodb_health else "Down",
    }
