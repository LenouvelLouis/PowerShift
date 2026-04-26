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

# Realistic EV charging profile (24 h, normalised 0–1)
# Source: PowerShift — Open-Meteo integration (6 charging channels, 16 BEVs, driving pattern CBS NL 2023)
# Peak at 18h–19h (evening return), zero at 07h & 17h (commute)
_EV_BASE_PROFILE: list[float] = [
    0.3730, 0.3730, 0.3730, 0.3730, 0.3730, 0.3730,  # 00h–05h home overnight
    0.3730, 0.0000, 0.0000, 0.1235, 0.1750, 0.1750,  # 06h–11h commute + work
    0.5961, 0.5961, 0.5961, 0.5961, 0.5961, 0.0000,  # 12h–17h work + fast charge
    1.0000, 1.0000, 0.5274, 0.5274, 0.5274, 0.3730,  # 18h–23h evening peak
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


# Residential time-of-day shape (24 h, normalized 0–1)
# Source: CBS Netherlands 2023 — weighted average of 10 household profiles
# Morning peak ~08h, evening peak ~18h, night trough ~03h
_HOUSE_TOD_PROFILE: list[float] = [
    0.3158, 0.2566, 0.2221, 0.2007, 0.2424, 0.3605,  # 00h–05h night
    0.6285, 0.8392, 0.8646, 0.7221, 0.6536, 0.6808,  # 06h–11h morning peak
    0.7263, 0.6808, 0.6454, 0.7127, 0.8320, 0.9960,  # 12h–17h afternoon
    1.0000, 0.9439, 0.8507, 0.7620, 0.6388, 0.4435,  # 18h–23h evening peak
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
