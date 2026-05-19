from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/content_engine"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    ELEVENLABS_API_KEY: Optional[str] = None
    PEXELS_API_KEY: Optional[str] = None
    ZERNIO_API_KEY: Optional[str] = None
    ZERNIO_TIKTOK_ACCOUNT_ID: Optional[str] = None
    
    STORAGE_PATH: str = "./storage/media"
    
    # Celery settings
    CELERY_BROKER_URL: str = REDIS_URL
    CELERY_RESULT_BACKEND: str = REDIS_URL
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
