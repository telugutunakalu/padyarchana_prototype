"""
Configuration settings for Padyarchana application.
"""
from pathlib import Path
from typing import List, Set

from pydantic_settings import BaseSettings


# Sentinel default values. The app refuses to start in non-development
# environments while any of these are still in force — see _check_prod_defaults.
DEV_DEFAULT_SESSION_SECRET = "dev-only-change-me-in-production"
DEV_DEFAULT_ADMIN_PASSWORD = "changeme"
DEV_DEFAULT_VIEWER_PASSWORD = "viewer"


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

    # Auth (development defaults — must be overridden via .env in production)
    SESSION_SECRET: str = DEV_DEFAULT_SESSION_SECRET
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = DEV_DEFAULT_ADMIN_PASSWORD
    VIEWER_USERNAME: str = "viewer"
    VIEWER_PASSWORD: str = DEV_DEFAULT_VIEWER_PASSWORD

    class Config:
        env_file = ".env"
        case_sensitive = True


def _check_prod_defaults(s: Settings) -> None:
    """Fail loudly if a non-development deployment is still using the
    development-default secrets / passwords baked into source."""
    if s.ENVIRONMENT == "development":
        return
    bad = []
    if s.SESSION_SECRET == DEV_DEFAULT_SESSION_SECRET or not s.SESSION_SECRET:
        bad.append("SESSION_SECRET")
    if s.ADMIN_PASSWORD == DEV_DEFAULT_ADMIN_PASSWORD:
        bad.append("ADMIN_PASSWORD")
    if s.VIEWER_PASSWORD == DEV_DEFAULT_VIEWER_PASSWORD:
        bad.append("VIEWER_PASSWORD")
    if bad:
        raise RuntimeError(
            f"Refusing to start: ENVIRONMENT={s.ENVIRONMENT!r} but still using "
            f"development defaults for {', '.join(bad)}. Set these in .env."
        )


# Global settings instance
settings = Settings()
_check_prod_defaults(settings)
