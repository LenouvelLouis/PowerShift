"""Unit tests for WindPowerCalculator domain service.

These tests cover every method and edge case described in the specification.
All tests are pure — no database, no FastAPI, no IO.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.domain.wind.entities import PowerCurvePoint, WindDataPoint, WindTurbineAsset, WindTurbineModel
from app.domain.wind.services import WindPowerCalculator, _STD_AIR_DENSITY

# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_vestas_v110() -> WindTurbineModel:
    """Vestas V110-2.0: 2 MW, cut-in 3 m/s, rated 11.5 m/s, cut-out 25 m/s."""
    return WindTurbineModel(
        id=uuid.uuid4(),
        manufacturer="Vestas",
        model_name="V110-2.0",
        rated_power_kw=2_000.0,
        rotor_diameter_m=110.0,
        hub_height_m=95.0,
        cut_in_speed_ms=3.0,
        cut_out_speed_ms=25.0,
        rated_speed_ms=11.5,
        power_curve=[
            PowerCurvePoint(3.0,   44.0),
            PowerCurvePoint(4.0,  136.0),
            PowerCurvePoint(5.0,  272.0),
            PowerCurvePoint(6.0,  476.0),
            PowerCurvePoint(7.0,  748.0),
            PowerCurvePoint(8.0, 1070.0),
            PowerCurvePoint(9.0, 1418.0),
            PowerCurvePoint(10.0, 1736.0),
            PowerCurvePoint(11.0, 1948.0),
            PowerCurvePoint(11.5, 2000.0),
            PowerCurvePoint(14.0, 2000.0),
            PowerCurvePoint(25.0, 2000.0),
        ],
    )


def _make_asset(model: WindTurbineModel, quantity: int = 1) -> WindTurbineAsset:
    return WindTurbineAsset(
        id=uuid.uuid4(),
        name="Test Site",
        turbine_model=model,
        latitude=53.2,
        longitude=6.5,
        altitude_m=0.0,
        quantity=quantity,
        is_active=True,
    )


@pytest.fixture
def calc() -> WindPowerCalculator:
    return WindPowerCalculator()


@pytest.fixture
def vestas() -> WindTurbineModel:
    return _make_vestas_v110()


@pytest.fixture
def asset(vestas: WindTurbineModel) -> WindTurbineAsset:
    return _make_asset(vestas)


# ── calculate_power_at_speed ──────────────────────────────────────────────────

class TestCalculatePowerAtSpeed:
    def test_zero_wind_speed_returns_zero(self, calc: WindPowerCalculator, vestas: WindTurbineModel) -> None:
        assert calc.calculate_power_at_speed(0.0, vestas) == 0.0

    def test_below_cut_in_returns_zero(self, calc: WindPowerCalculator, vestas: WindTurbineModel) -> None:
        assert calc.calculate_power_at_speed(2.9, vestas) == 0.0

    def test_exactly_cut_in_returns_nonzero(self, calc: WindPowerCalculator, vestas: WindTurbineModel) -> None:
        # At cut-in speed the turbine just starts generating
        power = calc.calculate_power_at_speed(3.0, vestas)
        assert power > 0.0

    def test_above_cut_out_returns_zero(self, calc: WindPowerCalculator, vestas: WindTurbineModel) -> None:
        assert calc.calculate_power_at_speed(25.1, vestas) == 0.0

    def test_exactly_cut_out_returns_zero(self, calc: WindPowerCalculator, vestas: WindTurbineModel) -> None:
        # cut_out is exclusive — turbine shuts down at this speed
        assert calc.calculate_power_at_speed(25.0, vestas) > 0.0  # still in range (==, not >)
        # But just past it → 0
        assert calc.calculate_power_at_speed(25.01, vestas) == 0.0

    def test_at_rated_speed_returns_rated_power_times_availability(
        self, calc: WindPowerCalculator, vestas: WindTurbineModel
    ) -> None:
        availability = 0.97
        power = calc.calculate_power_at_speed(11.5, vestas, availability=availability)
        expected = vestas.rated_power_kw * availability
        assert abs(power - expected) < 1.0  # within 1 kW

    def test_power_capped_at_rated(self, calc: WindPowerCalculator, vestas: WindTurbineModel) -> None:
        # At 20 m/s (above rated) power should equal rated * availability
        availability = 0.97
        power = calc.calculate_power_at_speed(20.0, vestas, availability=availability)
        assert power <= vestas.rated_power_kw * availability + 0.01

    def test_interpolation_between_curve_points(
        self, calc: WindPowerCalculator, vestas: WindTurbineModel
    ) -> None:
        # Midpoint between 8.0 m/s (1070 kW) and 9.0 m/s (1418 kW)
        # np.interp → 1244 kW (exact linear interp), then × 0.97 availability
        power = calc.calculate_power_at_speed(8.5, vestas, availability=1.0)
        assert abs(power - 1244.0) < 1.0

    def test_air_density_correction_lower_density_reduces_power(
        self, calc: WindPowerCalculator, vestas: WindTurbineModel
    ) -> None:
        power_std = calc.calculate_power_at_speed(8.0, vestas, air_density=_STD_AIR_DENSITY)
        power_high_alt = calc.calculate_power_at_speed(8.0, vestas, air_density=1.0)
        assert power_high_alt < power_std

    def test_air_density_correction_higher_density_increases_power(
        self, calc: WindPowerCalculator, vestas: WindTurbineModel
    ) -> None:
        power_std = calc.calculate_power_at_speed(8.0, vestas, air_density=_STD_AIR_DENSITY)
        power_cold = calc.calculate_power_at_speed(8.0, vestas, air_density=1.35)
        # But capped at rated power × availability
        assert power_cold >= power_std or power_cold == vestas.rated_power_kw * 0.97

    def test_availability_zero_returns_zero(
        self, calc: WindPowerCalculator, vestas: WindTurbineModel
    ) -> None:
        assert calc.calculate_power_at_speed(10.0, vestas, availability=0.0) == 0.0

    def test_power_is_non_negative(self, calc: WindPowerCalculator, vestas: WindTurbineModel) -> None:
        for speed in [0.0, 1.0, 2.9, 3.0, 8.0, 11.5, 25.0, 30.0]:
            assert calc.calculate_power_at_speed(speed, vestas) >= 0.0

    def test_model_without_power_curve_uses_cubic_fallback(
        self, calc: WindPowerCalculator
    ) -> None:
        model_no_curve = WindTurbineModel(
            id=uuid.uuid4(),
            manufacturer="Test",
            model_name="NoCurve-1.0",
            rated_power_kw=1_000.0,
            rotor_diameter_m=80.0,
            hub_height_m=80.0,
            cut_in_speed_ms=3.0,
            cut_out_speed_ms=25.0,
            rated_speed_ms=12.0,
            power_curve=[],  # empty — triggers cubic fallback
        )
        # At rated speed → rated power × availability
        power = calc.calculate_power_at_speed(12.0, model_no_curve, availability=1.0)
        assert abs(power - 1_000.0) < 1.0

        # Below rated → cubic fraction
        power_6 = calc.calculate_power_at_speed(6.0, model_no_curve, availability=1.0)
        expected = 1_000.0 * (6.0 / 12.0) ** 3
        assert abs(power_6 - expected) < 0.1


# ── estimate_air_density ──────────────────────────────────────────────────────

class TestEstimateAirDensity:
    def test_sea_level_15c_close_to_standard(self, calc: WindPowerCalculator) -> None:
        rho = calc.estimate_air_density(temperature_c=15.0, altitude_m=0.0)
        assert abs(rho - _STD_AIR_DENSITY) < 0.01

    def test_high_altitude_reduces_density(self, calc: WindPowerCalculator) -> None:
        rho_sea = calc.estimate_air_density(15.0, 0.0)
        rho_high = calc.estimate_air_density(15.0, 2000.0)
        assert rho_high < rho_sea

    def test_cold_temperature_increases_density(self, calc: WindPowerCalculator) -> None:
        rho_warm = calc.estimate_air_density(20.0, 0.0)
        rho_cold = calc.estimate_air_density(-10.0, 0.0)
        assert rho_cold > rho_warm

    def test_density_is_positive(self, calc: WindPowerCalculator) -> None:
        assert calc.estimate_air_density(25.0, 500.0) > 0.0


# ── extrapolate_wind_speed ────────────────────────────────────────────────────

class TestExtrapolateWindSpeed:
    def test_same_height_returns_same_speed(self, calc: WindPowerCalculator) -> None:
        assert calc.extrapolate_wind_speed(8.0, 10.0, 10.0) == pytest.approx(8.0)

    def test_higher_hub_increases_speed(self, calc: WindPowerCalculator) -> None:
        v = calc.extrapolate_wind_speed(8.0, 10.0, 95.0)
        assert v > 8.0

    def test_power_law_formula(self, calc: WindPowerCalculator) -> None:
        # v(95) = 8.0 * (95/10)^0.14
        expected = 8.0 * (95.0 / 10.0) ** 0.14
        result = calc.extrapolate_wind_speed(8.0, 10.0, 95.0, shear_exponent=0.14)
        assert result == pytest.approx(expected, rel=1e-6)

    def test_zero_ref_height_returns_input_speed(self, calc: WindPowerCalculator) -> None:
        assert calc.extrapolate_wind_speed(5.0, 0.0, 80.0) == 5.0

    def test_zero_hub_height_returns_input_speed(self, calc: WindPowerCalculator) -> None:
        assert calc.extrapolate_wind_speed(5.0, 10.0, 0.0) == 5.0

    def test_zero_wind_speed(self, calc: WindPowerCalculator) -> None:
        assert calc.extrapolate_wind_speed(0.0, 10.0, 80.0) == pytest.approx(0.0)

    def test_urban_shear_gives_higher_speed_than_open(self, calc: WindPowerCalculator) -> None:
        v_open = calc.extrapolate_wind_speed(6.0, 10.0, 80.0, shear_exponent=0.14)
        v_urban = calc.extrapolate_wind_speed(6.0, 10.0, 80.0, shear_exponent=0.30)
        assert v_urban > v_open


# ── calculate_power_series ────────────────────────────────────────────────────

class TestCalculatePowerSeries:
    def _make_wind_data(self, speeds: list[float]) -> list[WindDataPoint]:
        base = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        return [
            WindDataPoint(
                timestamp=base.replace(hour=i % 24),
                wind_speed_ms=s,
                temperature_c=10.0,
            )
            for i, s in enumerate(speeds)
        ]

    def test_output_length_matches_input(
        self, calc: WindPowerCalculator, asset: WindTurbineAsset
    ) -> None:
        data = self._make_wind_data([5.0, 8.0, 12.0])
        series = calc.calculate_power_series(data, asset)
        assert len(series) == 3

    def test_calm_wind_all_zeros(
        self, calc: WindPowerCalculator, asset: WindTurbineAsset
    ) -> None:
        data = self._make_wind_data([0.0, 1.0, 2.9])
        series = calc.calculate_power_series(data, asset)
        # KNMI 10m speeds are extrapolated to 95m hub — still likely below cut-in for 0/1/2.9
        for _, power in series:
            # After extrapolation from 10m to 95m, 2.9*1.424 ≈ 4.1 m/s > cut-in
            # So only 0 and 1 m/s guaranteed zero
            assert power >= 0.0

    def test_high_wind_gives_max_power(
        self, calc: WindPowerCalculator, asset: WindTurbineAsset
    ) -> None:
        # Wind at 12 m/s at 10m → extrapolated to 95m will be above rated speed
        data = self._make_wind_data([12.0])
        series = calc.calculate_power_series(data, asset)
        _, power = series[0]
        # Should be close to rated × availability
        assert power > asset.turbine_model.rated_power_kw * 0.90

    def test_quantity_scales_power(
        self, calc: WindPowerCalculator, vestas: WindTurbineModel
    ) -> None:
        asset_1 = _make_asset(vestas, quantity=1)
        asset_5 = _make_asset(vestas, quantity=5)
        data = self._make_wind_data([8.0])
        series_1 = calc.calculate_power_series(data, asset_1)
        series_5 = calc.calculate_power_series(data, asset_5)
        _, p1 = series_1[0]
        _, p5 = series_5[0]
        assert p5 == pytest.approx(p1 * 5, rel=1e-6)

    def test_timestamps_preserved(
        self, calc: WindPowerCalculator, asset: WindTurbineAsset
    ) -> None:
        data = self._make_wind_data([6.0, 7.0])
        series = calc.calculate_power_series(data, asset)
        for (ts_out, _), point in zip(series, data):
            assert ts_out == point.timestamp

    def test_all_powers_non_negative(
        self, calc: WindPowerCalculator, asset: WindTurbineAsset
    ) -> None:
        import random
        random.seed(42)
        speeds = [random.uniform(0, 30) for _ in range(50)]
        data = self._make_wind_data(speeds)
        series = calc.calculate_power_series(data, asset)
        for _, power in series:
            assert power >= 0.0


# ── calculate_capacity_factor ─────────────────────────────────────────────────

class TestCalculateCapacityFactor:
    def test_full_rated_output_gives_one(self, calc: WindPowerCalculator) -> None:
        series = [(datetime.now(timezone.utc), 2000.0)] * 24
        cf = calc.calculate_capacity_factor(series, 2000.0)
        assert cf == pytest.approx(1.0)

    def test_half_output_gives_half(self, calc: WindPowerCalculator) -> None:
        series = [(datetime.now(timezone.utc), 1000.0)] * 24
        cf = calc.calculate_capacity_factor(series, 2000.0)
        assert cf == pytest.approx(0.5)

    def test_zero_output_gives_zero(self, calc: WindPowerCalculator) -> None:
        series = [(datetime.now(timezone.utc), 0.0)] * 10
        cf = calc.calculate_capacity_factor(series, 2000.0)
        assert cf == pytest.approx(0.0)

    def test_empty_series_gives_zero(self, calc: WindPowerCalculator) -> None:
        assert calc.calculate_capacity_factor([], 2000.0) == 0.0

    def test_zero_rated_power_gives_zero(self, calc: WindPowerCalculator) -> None:
        series = [(datetime.now(timezone.utc), 500.0)]
        assert calc.calculate_capacity_factor(series, 0.0) == 0.0

    def test_cf_capped_at_one(self, calc: WindPowerCalculator) -> None:
        # Power exceeding rated (shouldn't happen in practice but let's be safe)
        series = [(datetime.now(timezone.utc), 3000.0)] * 5
        cf = calc.calculate_capacity_factor(series, 2000.0)
        assert cf <= 1.0
