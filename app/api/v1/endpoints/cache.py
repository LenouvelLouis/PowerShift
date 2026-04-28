"""Cache management endpoints — stats and invalidation for the weather profile cache."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import BaseModel

from app.infrastructure.cache.weather_cache import get_weather_cache

router = APIRouter(prefix="/cache", tags=["Cache"])


class CacheStatsResponse(BaseModel):
    """Schema returned by GET /cache/stats."""

    size: int
    hits: int
    misses: int


@router.get("/stats", response_model=CacheStatsResponse)
async def cache_stats() -> CacheStatsResponse:
    """Return current weather cache statistics (size, hit/miss counts)."""
    stats = await get_weather_cache().stats()
    return CacheStatsResponse(size=stats.size, hits=stats.hits, misses=stats.misses)


@router.delete("", status_code=204, response_class=Response)
async def cache_clear() -> Response:
    """Clear all cached weather profiles and reset counters."""
    await get_weather_cache().clear()
    return Response(status_code=204)
