from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os

class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "AI Clipper"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database & Cache
    DATABASE_URL: str = "postgresql+asyncpg://clipper:clipperpass@postgres:5432/clipper_db"
    DATABASE_SYNC_URL: str = "postgresql+psycopg2://clipper:clipperpass@postgres:5432/clipper_db"
    REDIS_URL: str = "redis://redis:6379/0"

    # Security & Encryption
    KEY_ENCRYPTION_SECRET: str
    JWT_SECRET: str = "default_dev_secret_please_change"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Storage & Limits
    STORAGE_PATH: str = "./storage"
    MAX_VIDEO_MINUTES: int = 60
    MAX_FILE_SIZE_MB: int = 500
    MAX_PARALLEL_JOBS_PER_USER: int = 3
    TEMP_FILE_RETENTION_HOURS: int = 24

    # AI Defaults
    WHISPER_MODEL: str = "base"

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

settings = Settings()
