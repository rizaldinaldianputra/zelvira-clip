from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy import create_engine
from contextlib import contextmanager
from typing import AsyncGenerator
from app.core.config import settings

# Base class for all ORM models
Base = declarative_base()

# Async engine for FastAPI endpoints
async_engine_kwargs = {
    "echo": False,
    "pool_pre_ping": True,
}
if not settings.DATABASE_URL.startswith("sqlite"):
    async_engine_kwargs["pool_size"] = 10
    async_engine_kwargs["max_overflow"] = 20

async_engine = create_async_engine(
    settings.DATABASE_URL,
    **async_engine_kwargs
)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession
)

# Sync engine for Celery tasks & Alembic
sync_url = settings.DATABASE_SYNC_URL
if sync_url.startswith("postgresql://"):
    sync_url = sync_url.replace("postgresql://", "postgresql+psycopg2://", 1)

sync_engine_kwargs = {
    "echo": False,
    "pool_pre_ping": True,
}
if not sync_url.startswith("sqlite"):
    sync_engine_kwargs["pool_size"] = 10
    sync_engine_kwargs["max_overflow"] = 20

sync_engine = create_engine(
    sync_url,
    **sync_engine_kwargs
)
SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for async database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

@contextmanager
def get_sync_db():
    """Context manager for synchronous database sessions (used by Celery workers)."""
    session: Session = SyncSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
