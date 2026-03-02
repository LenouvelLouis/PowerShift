"""Application settings — loaded from .env, optionally overridden by Azure Key Vault."""

from functools import lru_cache

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
    DATABASE_URL: str = ""

    # Azure Key Vault (optional)
    AZURE_KEY_VAULT_URL: str = ""
    AKV_SECRET_DATABASE_URL: str = "energy-grid-database-url"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


# Singleton instance used across the application
settings = Settings()
