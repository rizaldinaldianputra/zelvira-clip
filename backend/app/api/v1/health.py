from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as aioredis
from app.core.config import settings
from app.core.database import get_db

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    db_status = "ok"
    redis_status = "ok"

    # Test database
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    # Test Redis
    try:
        r = aioredis.from_url(settings.REDIS_URL)
        await r.ping()
        await r.close()
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"

    overall = "ok" if db_status == "ok" and redis_status == "ok" else "degraded"

    return {
        "status": overall,
        "database": db_status,
        "redis": redis_status,
        "project": settings.PROJECT_NAME
    }
