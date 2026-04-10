"""Residential house demand entity.

Profile source: CBS Netherlands 2023 — Energy consumption private dwellings
Reference: cbs.nl/en-gb/figures/detail/81528ENG + Energie-Nederland

Based on a weighted average of 10 Dutch household profiles (500 households,
Groningen village simulation), covering:
  - single_person:   1800–2000 kWh/year
  - couple_no_kids:  2600–2800 kWh/year
  - family_small:    3200–3500 kWh/year
  - family_large:    3800–4200 kWh/year
  - elderly:         1600–2400 kWh/year

National average: 2740 kWh/household/year (CBS 2023).
Weights = annual_kwh per household type (energy-proportional mix).

Peak at 18h–19h (evening cooking + appliances), morning peak at 08h–09h,
night trough at 03h–04h.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from app.domain.entities.demand.base_demand import BaseDemand

# Weighted average of 10 CBS household profiles, normalized to [0.0, 1.0].
_RESIDENTIAL_PROFILE: list[float] = [
    0.3158, 0.2566, 0.2221, 0.2007, 0.2424, 0.3605,  # 00h–05h night
    0.6285, 0.8392, 0.8646, 0.7221, 0.6536, 0.6808,  # 06h–11h morning peak
    0.7263, 0.6808, 0.6454, 0.7127, 0.8320, 0.9960,  # 12h–17h afternoon
    1.0000, 0.9439, 0.8507, 0.7620, 0.6388, 0.4435,  # 18h–23h evening peak
]


@dataclass
class House(BaseDemand):
    def get_type(self) -> str:
        return "house"

    def get_load_profile(self) -> Sequence[float]:
        return _RESIDENTIAL_PROFILE
