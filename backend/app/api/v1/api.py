from fastapi import APIRouter
from app.api.v1 import auth, jobs, clips, settings, health, ai_gateway

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(jobs.router)
api_router.include_router(clips.router)
api_router.include_router(settings.router)
api_router.include_router(ai_gateway.router)
