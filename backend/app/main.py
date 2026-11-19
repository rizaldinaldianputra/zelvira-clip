from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logging import logger
from app.core.database import async_engine, Base
from app.api.v1.api import api_router
from app.api.v1.health import router as health_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing AI Clipper Backend...")
    # Create tables automatically on startup if using SQLite or quick dev
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema initialized.")
    except Exception as e:
        logger.warning(f"Could not auto-create tables on startup: {e}")
    yield
    logger.info("Shutting down AI Clipper Backend...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for AI Clipper - Automated streamer highlights and 9:16 vertical clips.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler to prevent any secret leak in responses
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    err_str = str(exc)
    logger.error(f"Unhandled Exception on {request.method} {request.url.path}: {err_str}")
    # Generic sanitized message for unexpected internal errors
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please check server logs."}
    )

# Include root health check (GET /health) as requested in Prompt 2
app.include_router(health_router)

# Include API v1 router (prefix /api/v1)
app.include_router(api_router)
