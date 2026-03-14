"""Load profile provider backed by the Open-Meteo API (free, no API key required).

Strategy:
- Fetch hourly temperature for Groningen for the requested duration.
  - If start_date is provided: use the historical archive API (aligned to simulation period).
  - Otherwise: use the forecast API (current weather).
- Convert temperature to a normalized demand profile per demand type:
    - house          : heating + cooling + base load
    - electric_vehicle: overnight charging, boosted when cold
    - (others)       : flat profile
- If the API is unavailable, fall back to a flat profile.
"""

from __future__ import annotations

import math
from datetime import date, timedelta

import httpx

from app.domain.interfaces.load_profile_provider import ILoadProfileProvider

_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
_DEFAULT_LAT = 53.2194   # Groningen
_DEFAULT_LON = 6.5665

# Typical EV overnight charging shape (24 h, normalised 0–1)
_EV_BASE_PROFILE: list[float] = [
    0.80, 0.90, 1.00, 0.95, 0.70, 0.40,
    0.20, 0.10, 0.10, 0.10, 0.15, 0.20,
    0.20, 0.20, 0.15, 0.10, 0.15, 0.30,
    0.50, 0.60, 0.70, 0.75, 0.80, 0.85,
]


class OpenMeteoLoadProfileProvider(ILoadProfileProvider):
    """Derives hourly demand profiles from Open-Meteo temperature data."""

    async def get_profile(self, demand_type: str, hours: int, start_date: date | None = None) -> list[float]:
        temps = await self._fetch_temperatures(hours, start_date)
        return _temperature_to_profile(demand_type, temps)

    @staticmethod
    async def _fetch_temperatures(hours: int, start_date: date | None) -> list[float]:
        forecast_days = min(16, math.ceil(hours / 24))
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                if start_date is not None:
                    end_date = start_date + timedelta(days=forecast_days)
                    resp = await client.get(
                        _ARCHIVE_URL,
                        params={
                            "latitude": _DEFAULT_LAT,
                            "longitude": _DEFAULT_LON,
                            "hourly": "temperature_2m",
                            "start_date": start_date.isoformat(),
                            "end_date": end_date.isoformat(),
                            "timezone": "Europe/Amsterdam",
                        },
                    )
                else:
                    resp = await client.get(
                        _FORECAST_URL,
                        params={
                            "latitude": _DEFAULT_LAT,
                            "longitude": _DEFAULT_LON,
                            "hourly": "temperature_2m",
                            "forecast_days": forecast_days,
                            "timezone": "Europe/Amsterdam",
                        },
                    )
                resp.raise_for_status()
                temps: list[float] = resp.json()["hourly"]["temperature_2m"]
        except Exception:
            temps = [15.0] * (forecast_days * 24)

        while len(temps) < hours:
            temps = temps + temps
        return temps[:hours]


def _temperature_to_profile(demand_type: str, temps: list[float]) -> list[float]:
    if demand_type == "house":
        return _house_profile(temps)
    if demand_type == "electric_vehicle":
        return _ev_profile(temps)
    return [1.0] * len(temps)


# Typical residential time-of-day shape (24 h, normalized 0–1)
# Morning peak ~8h, evening peak ~19-21h, night trough ~3-5h
_HOUSE_TOD_PROFILE: list[float] = [
    0.45, 0.40, 0.38, 0.37, 0.38, 0.45,  # 0h–5h   night / early morning
    0.60, 0.80, 0.95, 0.85, 0.75, 0.70,  # 6h–11h  morning peak
    0.68, 0.65, 0.63, 0.65, 0.72, 0.85,  # 12h–17h afternoon
    0.95, 1.00, 0.98, 0.90, 0.75, 0.60,  # 18h–23h evening peak
]


def _house_profile(temps: list[float]) -> list[float]:
    raw = []
    for i, t in enumerate(temps):
        hour = i % 24
        tod = _HOUSE_TOD_PROFILE[hour]
        heating = max(0.0, (18.0 - t) / 30.0)
        cooling = max(0.0, (t - 22.0) / 20.0)
        thermal = 0.30 + heating + cooling
        raw.append(tod * thermal)
    return _normalize(raw)


def _ev_profile(temps: list[float]) -> list[float]:
    result = []
    for i, t in enumerate(temps):
        hour = i % 24
        cold_bonus = max(0.0, (5.0 - t) / 20.0) * 0.20
        result.append(min(1.0, _EV_BASE_PROFILE[hour] + cold_bonus))
    return result


def _normalize(values: list[float]) -> list[float]:
    max_v = max(values) if values else 1.0
    if max_v == 0:
        return [0.0] * len(values)
    return [v / max_v for v in values]
