"""Settings resolution."""

from __future__ import annotations

from functools import lru_cache

from app.config import Settings


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings instance loaded from .env."""
    return Settings()
