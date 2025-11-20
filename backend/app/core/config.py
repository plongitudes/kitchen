from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Roanes Kitchen"
    debug: bool = True
    environment: str = "development"

    # Database
    database_url: str = "postgresql+asyncpg://admin:admin@postgres:5432/roanes_kitchen"

    # Security
    jwt_secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_days: int = 7

    # Discord Bot (Optional - for meal plan notifications)
    discord_bot_token: Optional[str] = None
    discord_notification_channel_id: Optional[str] = None
    discord_test_channel_id: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
