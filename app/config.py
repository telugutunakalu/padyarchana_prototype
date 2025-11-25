"""
Configuration settings for Padyarchana application.
"""
from pathlib import Path
from typing import List, Set

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Application
    APP_NAME: str = "పద్యార్చన - Padyarchana"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./padyarchana.db"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:8000", "http://127.0.0.1:8000"]

    # Pagination
    DEFAULT_PAGE_SIZE: int = 10
    MAX_PAGE_SIZE: int = 100

    # Search
    SEARCH_RESULTS_LIMIT: int = 100

    # Paths
    STATIC_DIR: str = "static"
    TEMPLATES_DIR: str = "app/templates"
    DATA_DIR: str = "data"

    # Audio Settings
    AUDIO_DIR: Path = Path("static/audio/poems")
    MAX_AUDIO_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_AUDIO_FORMATS: Set[str] = {"mp3", "wav"}

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
