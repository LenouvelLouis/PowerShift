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

    # CORS — comma-separated allowed origins
    CORS_ORIGINS: str = "http://localhost:80,http://localhost:3000"
    # Optional frontend URL appended to the origins list when non-empty
    FRONTEND_URL: str = ""

    # Weather cache TTL (seconds) — how long solar/wind profiles stay cached in memory
    WEATHER_CACHE_TTL_SECONDS: int = 3600

    # Authentication — empty means auth is disabled (dev mode)
    API_KEY: str = ""

    # Database (PostgreSQL — Docker local or NeonDB cloud)
    DATABASE_URL: str = "postgresql+asyncpg://powershift:powershift@localhost:5432/powershift"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


# Singleton instance used across the application
settings = Settings()
