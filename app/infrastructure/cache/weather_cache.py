"""In-memory cache for weather profiles (solar irradiance, wind power).

Avoids redundant DB/API calls when the same date range is requested
multiple times (e.g. repeated simulation previews with small parameter tweaks).

Cache key: hash of (profile_type, start_date, end_date).
Cache value: list[float] (normalized 0.0-1.0 capacity factors per hour).
TTL: configurable via WEATHER_CACHE_TTL_SECONDS (default 3600 s / 1 hour).
"""

from __future__ import annotations

import asyncio
import hashlib
import time
from dataclasses import dataclass
from datetime import date


@dataclass(slots=True)
class _CacheEntry:
    """Single cached weather profile with creation timestamp."""

    data: list[float]
    created_at: float  # time.monotonic() seconds


@dataclass
class CacheStats:
    """Counters exposed via the /api/v1/cache/stats endpoint."""

    size: int = 0
    hits: int = 0
    misses: int = 0


class WeatherCache:
    """Thread-safe, TTL-aware in-memory cache for weather profile data.

    All public methods are async so they can be called from FastAPI handlers
    without blocking the event loop (even though the underlying dict operations
    are O(1) and effectively instant).
    """

    def __init__(self, ttl_seconds: int = 3600) -> None:
        self._ttl = ttl_seconds
        self._store: dict[str, _CacheEntry] = {}
        self._lock = asyncio.Lock()
        self._hits: int = 0
        self._misses: int = 0

    @staticmethod
    def _make_key(profile_type: str, start_date: date, end_date: date) -> str:
        """Deterministic cache key from profile parameters."""
        raw = f"{profile_type}:{start_date.isoformat()}:{end_date.isoformat()}"
        return hashlib.sha256(raw.encode()).hexdigest()

    async def get(self, profile_type: str, start_date: date, end_date: date) -> list[float] | None:
        """Return cached profile or None if missing/expired."""
        key = self._make_key(profile_type, start_date, end_date)
        async with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._misses += 1
                return None
            if time.monotonic() - entry.created_at >= self._ttl:
                del self._store[key]
                self._misses += 1
                return None
            self._hits += 1
            return entry.data

    async def set(self, profile_type: str, start_date: date, end_date: date, data: list[float]) -> None:
        """Store a profile in the cache."""
        key = self._make_key(profile_type, start_date, end_date)
        async with self._lock:
            self._store[key] = _CacheEntry(data=data, created_at=time.monotonic())

    async def clear(self) -> None:
        """Remove all entries and reset counters."""
        async with self._lock:
            self._store.clear()
            self._hits = 0
            self._misses = 0

    async def stats(self) -> CacheStats:
        """Return current cache statistics."""
        async with self._lock:
            # Evict expired entries before reporting size
            now = time.monotonic()
            expired = [k for k, v in self._store.items() if now - v.created_at >= self._ttl]
            for k in expired:
                del self._store[k]
            return CacheStats(size=len(self._store), hits=self._hits, misses=self._misses)


# ── Module-level singleton ──────────────────────────────────────────────────
# Lazily initialised with TTL from settings on first access via get_weather_cache().
_instance: WeatherCache | None = None


def get_weather_cache() -> WeatherCache:
    """Return the global WeatherCache singleton (created on first call)."""
    global _instance  # noqa: PLW0603
    if _instance is None:
        from app.config import settings

        _instance = WeatherCache(ttl_seconds=settings.WEATHER_CACHE_TTL_SECONDS)
    return _instance
