"""Unit tests for the in-memory weather cache."""

from __future__ import annotations

import asyncio
import time
from datetime import date
from unittest.mock import patch

import pytest

from app.infrastructure.cache.weather_cache import WeatherCache


@pytest.fixture()
def cache() -> WeatherCache:
    return WeatherCache(ttl_seconds=60)


@pytest.mark.asyncio
async def test_get_returns_none_on_miss(cache: WeatherCache) -> None:
    result = await cache.get("solar", date(2025, 6, 1), date(2025, 6, 2))
    assert result is None


@pytest.mark.asyncio
async def test_set_then_get_returns_data(cache: WeatherCache) -> None:
    data = [0.0, 0.5, 1.0, 0.3]
    await cache.set("solar", date(2025, 6, 1), date(2025, 6, 2), data)
    result = await cache.get("solar", date(2025, 6, 1), date(2025, 6, 2))
    assert result == data


@pytest.mark.asyncio
async def test_different_profile_type_is_separate_key(cache: WeatherCache) -> None:
    solar_data = [0.1, 0.2]
    wind_data = [0.8, 0.9]
    await cache.set("solar", date(2025, 6, 1), date(2025, 6, 2), solar_data)
    await cache.set("wind", date(2025, 6, 1), date(2025, 6, 2), wind_data)

    assert await cache.get("solar", date(2025, 6, 1), date(2025, 6, 2)) == solar_data
    assert await cache.get("wind", date(2025, 6, 1), date(2025, 6, 2)) == wind_data


@pytest.mark.asyncio
async def test_different_dates_are_separate_keys(cache: WeatherCache) -> None:
    d1 = [0.1]
    d2 = [0.9]
    await cache.set("solar", date(2025, 6, 1), date(2025, 6, 1), d1)
    await cache.set("solar", date(2025, 7, 1), date(2025, 7, 1), d2)

    assert await cache.get("solar", date(2025, 6, 1), date(2025, 6, 1)) == d1
    assert await cache.get("solar", date(2025, 7, 1), date(2025, 7, 1)) == d2


@pytest.mark.asyncio
async def test_expired_entry_returns_none() -> None:
    cache = WeatherCache(ttl_seconds=0)  # expire immediately
    await cache.set("solar", date(2025, 1, 1), date(2025, 1, 1), [1.0])
    # After TTL=0, any monotonic advance means expired
    result = await cache.get("solar", date(2025, 1, 1), date(2025, 1, 1))
    assert result is None


@pytest.mark.asyncio
async def test_clear_removes_all_entries(cache: WeatherCache) -> None:
    await cache.set("solar", date(2025, 1, 1), date(2025, 1, 1), [0.5])
    await cache.set("wind", date(2025, 1, 1), date(2025, 1, 1), [0.3])
    await cache.clear()

    assert await cache.get("solar", date(2025, 1, 1), date(2025, 1, 1)) is None
    assert await cache.get("wind", date(2025, 1, 1), date(2025, 1, 1)) is None


@pytest.mark.asyncio
async def test_stats_counters(cache: WeatherCache) -> None:
    await cache.set("solar", date(2025, 1, 1), date(2025, 1, 1), [0.5])

    # 1 hit
    await cache.get("solar", date(2025, 1, 1), date(2025, 1, 1))
    # 1 miss
    await cache.get("wind", date(2025, 1, 1), date(2025, 1, 1))

    stats = await cache.stats()
    assert stats.size == 1
    assert stats.hits == 1
    assert stats.misses == 1


@pytest.mark.asyncio
async def test_stats_evicts_expired_entries() -> None:
    cache = WeatherCache(ttl_seconds=0)
    await cache.set("solar", date(2025, 1, 1), date(2025, 1, 1), [0.5])
    stats = await cache.stats()
    assert stats.size == 0  # expired, so evicted during stats()


@pytest.mark.asyncio
async def test_clear_resets_counters(cache: WeatherCache) -> None:
    await cache.set("solar", date(2025, 1, 1), date(2025, 1, 1), [0.5])
    await cache.get("solar", date(2025, 1, 1), date(2025, 1, 1))
    await cache.get("wind", date(2025, 1, 1), date(2025, 1, 1))
    await cache.clear()

    stats = await cache.stats()
    assert stats.hits == 0
    assert stats.misses == 0
    assert stats.size == 0


@pytest.mark.asyncio
async def test_overwrite_existing_key(cache: WeatherCache) -> None:
    await cache.set("solar", date(2025, 1, 1), date(2025, 1, 1), [0.1])
    await cache.set("solar", date(2025, 1, 1), date(2025, 1, 1), [0.9])
    result = await cache.get("solar", date(2025, 1, 1), date(2025, 1, 1))
    assert result == [0.9]
