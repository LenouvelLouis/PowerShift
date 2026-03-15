"""Application settings — loaded from .env."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application metadata
    APP_NAME: str = "Energy Grid API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Environment: development | staging | production
    ENVIRONMENT: str = "development"

    # Database (NeonDB / PostgreSQL)
    DATABASE_URL: str = "postgresql://neondb_owner:npg_OUMdt0gS5vkD@ep-silent-dream-albpp1df-pooler.c-3.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


# Singleton instance used across the application
settings = Settings()
