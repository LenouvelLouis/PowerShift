"""Electric vehicle demand entity.

Profile source: ISEP 2026 — EV Charging Power Profile
Based on real charging channel data (charging_channels.json)
and driving pattern data (driving_pattern.json).

Village model: 16 BEVs | N_households=500 | ev_share=0.06
km/day=30 | kWh/km=0.204 | horizon=24h

Charging channels used:
  - home_private:     52% energy share, 7.4 kW,  18h-07h (LV 400V, Type2 AC)
  - home_socket:       6% energy share, 2.3 kW,  18h-07h (LV 230V, standard)
  - public_near_home: 15% energy share, 11 kW,   18h-23h (LV 400V, Type2 AC)
  - public_elsewhere:  5% energy share, 11 kW,   10h-20h (LV 400V, Type2 AC)
  - work:             12% energy share, 11 kW,   09h-17h (LV 400V, Type2 AC)
  - fast_charging:     9% energy share, 50 kW,   12h-20h (MV 10kV, CCS Combo2)

Driving pattern:
  - Morning commute: 07h (15 km driven, car unavailable)
  - At work: 08h-16h (work charger available)
  - Evening commute: 17h (15 km driven, car unavailable)
  - At home: 18h-23h and 00h-06h (home charger available)

Peak demand: 207 kW @ 18h (evening return + home charging)
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from app.domain.entities.demand.base_demand import BaseDemand


def _build_ev_profile() -> list[float]:
    """Build a realistic 24h normalised EV charging profile.

    Methodology:
    - For each hour, sum the power contributions of active charging channels
    - Weight each channel by its energy_share
    - A channel is active if the car is available AND the hour falls within
      the channel's operating window
    - Normalise the result to [0.0, 1.0]

    Returns a list of 24 floats (one per hour, starting at 00h).
    """

    # Channels: (name, energy_share, power_kw, start_hour, end_hour)
    # end_hour is exclusive; channels that cross midnight wrap around
    channels = [
        ("home_private",     0.52,  7.4,  18, 7),
        ("home_socket",      0.06,  2.3,  18, 7),
        ("public_near_home", 0.15, 11.0,  18, 23),
        ("public_elsewhere", 0.05, 11.0,  10, 20),
        ("work",             0.12, 11.0,   9, 17),
        ("fast_charging",    0.09, 50.0,  12, 20),
    ]

    # Car availability per hour (from driving_pattern.json)
    # 0 = car on the road (unavailable for charging), 1 = available
    car_available = [
        1,  # 00h - at home sleeping
        1,  # 01h
        1,  # 02h
        1,  # 03h
        1,  # 04h
        1,  # 05h
        1,  # 06h
        0,  # 07h - morning commute (15 km)
        1,  # 08h - at work
        1,  # 09h
        1,  # 10h
        1,  # 11h
        1,  # 12h
        1,  # 13h
        1,  # 14h
        1,  # 15h
        1,  # 16h
        0,  # 17h - evening commute (15 km)
        1,  # 18h - at home
        1,  # 19h
        1,  # 20h
        1,  # 21h
        1,  # 22h
        1,  # 23h
    ]

    def is_channel_active(hour: int, start: int, end: int) -> bool:
        if start <= end:
            return start <= hour < end
        else:
            return hour >= start or hour < end

    raw_profile = []
    for h in range(24):
        if car_available[h] == 0:
            raw_profile.append(0.0)
            continue

        total_power = sum(
            share * power
            for _, share, power, start, end in channels
            if is_channel_active(h, start, end)
        )
        raw_profile.append(total_power)

    max_power = max(raw_profile) if max(raw_profile) > 0 else 1.0
    return [round(p / max_power, 4) for p in raw_profile]


_EV_PROFILE: list[float] = _build_ev_profile()


@dataclass
class ElectricVehicle(BaseDemand):
    def get_type(self) -> str:
        return "electric_vehicle"

    def get_load_profile(self) -> Sequence[float]:
        return _EV_PROFILE
