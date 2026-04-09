"""WindPowerCalculator — core domain service for wind power computation."""

from __future__ import annotations

import logging
import math
from datetime import datetime

import numpy as np

from app.domain.wind.entities import WindDataPoint, WindTurbineAsset, WindTurbineModel

_log = logging.getLogger(__name__)

_STD_AIR_DENSITY: float = 1.225  # kg/m³ at sea level, 15 °C
_P0: float = 101_325.0            # Standard atmosphere, Pa
_R_DRY: float = 287.05            # Specific gas constant for dry air, J/(kg·K)
_G: float = 9.81                  # Gravitational acceleration, m/s²


class WindPowerCalculator:
    """Stateless service that converts wind observations into power output.

    All methods are pure functions with no side effects.
    Dependencies (numpy) are imported at module level — no DB access here.
    """

    # ── Physical helpers ─────────────────────────────────────────────────────

    def estimate_air_density(self, temperature_c: float, altitude_m: float) -> float:
        """Estimate air density from temperature and altitude using barometric formula.

        Formula: ρ = (P₀ / (R · T)) · exp(−g · h / (R · T))

        Args:
            temperature_c: Ambient temperature in degrees Celsius.
            altitude_m: Site altitude above sea level in metres.

        Returns:
            Air density in kg/m³.
        """
        T = temperature_c + 273.15  # Convert to Kelvin
        rho = (_P0 / (_R_DRY * T)) * math.exp(-_G * altitude_m / (_R_DRY * T))
        _log.debug("Air density at %.0f m, %.1f °C → %.4f kg/m³", altitude_m, temperature_c, rho)
        return rho

    def extrapolate_wind_speed(
        self,
        speed_at_ref: float,
        ref_height_m: float,
        hub_height_m: float,
        shear_exponent: float = 0.14,
    ) -> float:
        """Extrapolate wind speed from reference height to hub height (power law).

        v(h) = v(h_ref) · (h / h_ref) ^ α

        Args:
            speed_at_ref: Measured wind speed at reference height (m/s).
            ref_height_m: Height of the measurement (e.g. 10 m for KNMI stations).
            hub_height_m: Turbine hub height in metres.
            shear_exponent: Wind shear exponent α.
                - 0.14 open terrain (default)
                - 0.20 suburban
                - 0.30 urban / forested

        Returns:
            Wind speed at hub height in m/s.
        """
        if ref_height_m <= 0 or hub_height_m <= 0:
            return speed_at_ref
        extrapolated = speed_at_ref * (hub_height_m / ref_height_m) ** shear_exponent
        _log.debug(
            "Wind extrapolation %.2f m/s @ %.0f m → %.2f m/s @ %.0f m (α=%.2f)",
            speed_at_ref, ref_height_m, extrapolated, hub_height_m, shear_exponent,
        )
        return extrapolated

    # ── Core power calculation ────────────────────────────────────────────────

    def calculate_power_at_speed(
        self,
        wind_speed_ms: float,
        turbine: WindTurbineModel,
        air_density: float = _STD_AIR_DENSITY,
        availability: float = 0.97,
    ) -> float:
        """Return power output in kW for a single wind speed.

        Steps:
        1. Return 0 if below cut-in or above cut-out.
        2. Interpolate the manufacturer power curve (or use cubic fallback).
        3. Apply air density correction factor ρ/ρ₀.
        4. Clamp to rated power.
        5. Apply availability factor.

        Args:
            wind_speed_ms: Hub-height wind speed in m/s.
            turbine: WindTurbineModel with power curve data.
            air_density: Actual air density in kg/m³ (default 1.225 kg/m³).
            availability: Fraction of time turbine is operational (default 0.97).

        Returns:
            Power output in kW (≥ 0).
        """
        if wind_speed_ms < turbine.cut_in_speed_ms or wind_speed_ms > turbine.cut_out_speed_ms:
            _log.debug(
                "Wind speed %.2f m/s outside operating range [%.1f, %.1f] → 0 kW",
                wind_speed_ms, turbine.cut_in_speed_ms, turbine.cut_out_speed_ms,
            )
            return 0.0

        if turbine.power_curve:
            speeds = [pt.wind_speed_ms for pt in turbine.power_curve]
            powers = [pt.power_kw for pt in turbine.power_curve]
            raw_power = float(np.interp(wind_speed_ms, speeds, powers))
            _log.debug("Power curve interpolation at %.2f m/s → %.1f kW", wind_speed_ms, raw_power)
        else:
            # Cubic approximation between cut-in and rated speed
            v_ratio = min(wind_speed_ms / turbine.rated_speed_ms, 1.0)
            raw_power = turbine.rated_power_kw * v_ratio ** 3
            _log.debug("Cubic fallback at %.2f m/s → %.1f kW", wind_speed_ms, raw_power)

        # Air density correction: power scales linearly with air density
        density_factor = air_density / _STD_AIR_DENSITY
        corrected_power = raw_power * density_factor

        # Never exceed rated power
        corrected_power = min(corrected_power, turbine.rated_power_kw)

        result = corrected_power * availability
        _log.debug(
            "Final power at %.2f m/s (ρ=%.4f kg/m³, avail=%.2f) → %.1f kW",
            wind_speed_ms, air_density, availability, result,
        )
        return result

    # ── Time-series ───────────────────────────────────────────────────────────

    def calculate_power_series(
        self,
        wind_data: list[WindDataPoint],
        asset: WindTurbineAsset,
        availability: float = 0.97,
    ) -> list[tuple[datetime, float]]:
        """Compute hourly power output for a sequence of wind observations.

        KNMI data is measured at 10 m; this method automatically extrapolates
        to the turbine hub height using the power law with α = 0.14.

        Args:
            wind_data: Ordered list of WindDataPoint observations.
            asset: WindTurbineAsset with turbine model and site details.
            availability: Turbine availability factor (default 0.97).

        Returns:
            List of (timestamp, total_power_kw) tuples, one per observation.
            Power is already multiplied by asset.quantity.
        """
        turbine = asset.turbine_model
        altitude_m = asset.altitude_m or 0.0
        results: list[tuple[datetime, float]] = []

        _log.debug(
            "Calculating power series for asset '%s' (%d × %s), %d data points",
            asset.name, asset.quantity, turbine.model_name, len(wind_data),
        )

        for point in wind_data:
            # Extrapolate from KNMI 10 m reference height to hub height
            hub_speed = self.extrapolate_wind_speed(
                point.wind_speed_ms, 10.0, turbine.hub_height_m
            )

            # Use measured temperature for density correction when available
            if point.temperature_c is not None:
                air_density = self.estimate_air_density(point.temperature_c, altitude_m)
            else:
                air_density = _STD_AIR_DENSITY

            power_per_turbine = self.calculate_power_at_speed(
                hub_speed, turbine, air_density, availability
            )
            total_power = power_per_turbine * asset.quantity
            results.append((point.timestamp, total_power))

        return results

    # ── Summary statistics ────────────────────────────────────────────────────

    def calculate_capacity_factor(
        self,
        power_series: list[tuple[datetime, float]],
        rated_power_kw: float,
    ) -> float:
        """Compute capacity factor: actual_energy / (rated_power × time_steps).

        Args:
            power_series: List of (timestamp, power_kw) tuples.
            rated_power_kw: Nameplate rated power of the turbine in kW.

        Returns:
            Capacity factor as a float in [0, 1].
        """
        if not power_series or rated_power_kw <= 0:
            return 0.0
        total_actual = sum(p for _, p in power_series)
        total_possible = rated_power_kw * len(power_series)
        return min(total_actual / total_possible, 1.0)
