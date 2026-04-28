"""Unit tests for weather data validation (fail-fast on all-zero profiles)."""

from __future__ import annotations

import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domain.interfaces.simulation_repository import SimulationRunInput
from app.domain.simulation.exceptions import WeatherDataEmptyError
from app.infrastructure.simulation.network_builder import PyPSANetworkBuilder


def _make_run_input(
    *,
    fail_on_empty_weather: bool = True,
    snapshot_hours: int = 24,
    start_date: date | None = None,
    end_date: date | None = None,
) -> SimulationRunInput:
    return SimulationRunInput(
        snapshot_hours=snapshot_hours,
        solver="highs",
        supply_ids=["s1"],
        demand_ids=[],
        network_ids=[],
        start_date=start_date or date(2025, 6, 1),
        end_date=end_date or date(2025, 6, 1),
        fail_on_empty_weather=fail_on_empty_weather,
    )


def _make_solar_supply(name: str = "Solar 1") -> MagicMock:
    supply = MagicMock()
    supply.name = name
    supply.id = uuid.uuid4()
    supply.get_carrier.return_value = "solar"
    supply.capacity_mw = 10.0
    return supply


def _make_wind_supply(name: str = "Wind 1") -> MagicMock:
    supply = MagicMock()
    supply.name = name
    supply.id = uuid.uuid4()
    supply.get_carrier.return_value = "wind"
    supply.capacity_mw = 5.0
    return supply


def _make_nuclear_supply(name: str = "Nuclear 1") -> MagicMock:
    supply = MagicMock()
    supply.name = name
    supply.id = uuid.uuid4()
    supply.get_carrier.return_value = "nuclear"
    supply.capacity_mw = 100.0
    return supply


class TestWeatherDataEmptyError:
    """Tests for the domain exception itself."""

    def test_stores_generator_names(self) -> None:
        err = WeatherDataEmptyError(["Solar 1", "Wind 1"])
        assert err.generator_names == ["Solar 1", "Wind 1"]

    def test_message_contains_generator_names(self) -> None:
        err = WeatherDataEmptyError(["Solar 1"])
        assert "Solar 1" in str(err)
        assert "all zero" in str(err).lower()

    def test_message_contains_date_hint(self) -> None:
        err = WeatherDataEmptyError(["Wind Farm"])
        assert "2025" in str(err)


class TestWeatherValidationInNetworkBuilder:
    """Tests for the fail-fast validation in PyPSANetworkBuilder.run()."""

    @pytest.mark.asyncio
    async def test_raises_when_solar_profile_all_zero_and_fail_on(self) -> None:
        pv_repo = AsyncMock()
        pv_repo.get_solar_profile.return_value = [0.0] * 24  # all-zero
        pv_repo.get_wind_profile.return_value = [0.5] * 24  # valid

        builder = PyPSANetworkBuilder(pv_profile_repo=pv_repo)
        solar = _make_solar_supply()
        run_input = _make_run_input(fail_on_empty_weather=True)

        with pytest.raises(WeatherDataEmptyError) as exc_info:
            await builder.run(run_input, supplies=[solar], demands=[], network_components=[])

        assert solar.name in exc_info.value.generator_names

    @pytest.mark.asyncio
    async def test_raises_when_wind_profile_all_zero_and_fail_on(self) -> None:
        pv_repo = AsyncMock()
        pv_repo.get_wind_profile.return_value = [0.0] * 24  # all-zero

        builder = PyPSANetworkBuilder(pv_profile_repo=pv_repo)
        wind = _make_wind_supply()
        run_input = _make_run_input(fail_on_empty_weather=True)

        with pytest.raises(WeatherDataEmptyError) as exc_info:
            await builder.run(run_input, supplies=[wind], demands=[], network_components=[])

        assert wind.name in exc_info.value.generator_names

    @pytest.mark.asyncio
    async def test_does_not_raise_when_fail_off(self) -> None:
        """When fail_on_empty_weather=False, all-zero profiles should only warn, not raise."""
        pv_repo = AsyncMock()
        pv_repo.get_solar_profile.return_value = [0.0] * 24

        sim = MagicMock()
        sim.run_sync.return_value = MagicMock(
            total_supply_mwh=0.0,
            total_demand_mwh=0.0,
            balance_mwh=0.0,
            status="optimized",
            objective_value=0.0,
            result_json={},
        )

        builder = PyPSANetworkBuilder(simulation=sim, pv_profile_repo=pv_repo)
        solar = _make_solar_supply()
        run_input = _make_run_input(fail_on_empty_weather=False)

        # Should NOT raise — proceeds with warning
        result = await builder.run(run_input, supplies=[solar], demands=[], network_components=[])
        assert result.status == "optimized"

    @pytest.mark.asyncio
    async def test_does_not_raise_for_nuclear_constant_profile(self) -> None:
        """Nuclear plants have constant profiles (p_max_pu=1.0) and should never trigger validation."""
        pv_repo = AsyncMock()
        # Nuclear won't call get_solar_profile or get_wind_profile

        sim = MagicMock()
        sim.run_sync.return_value = MagicMock(
            total_supply_mwh=100.0,
            total_demand_mwh=90.0,
            balance_mwh=10.0,
            status="optimized",
            objective_value=42.0,
            result_json={},
        )

        builder = PyPSANetworkBuilder(simulation=sim, pv_profile_repo=pv_repo)
        nuclear = _make_nuclear_supply()
        run_input = _make_run_input(fail_on_empty_weather=True)

        # Should NOT raise — nuclear is not weather-dependent
        result = await builder.run(run_input, supplies=[nuclear], demands=[], network_components=[])
        assert result.status == "optimized"

    @pytest.mark.asyncio
    async def test_does_not_raise_when_profiles_have_nonzero_values(self) -> None:
        """Valid weather profiles should never trigger the validation."""
        pv_repo = AsyncMock()
        pv_repo.get_solar_profile.return_value = [0.0, 0.1, 0.5, 0.8] + [0.3] * 20

        sim = MagicMock()
        sim.run_sync.return_value = MagicMock(
            total_supply_mwh=50.0,
            total_demand_mwh=40.0,
            balance_mwh=10.0,
            status="optimized",
            objective_value=10.0,
            result_json={},
        )

        builder = PyPSANetworkBuilder(simulation=sim, pv_profile_repo=pv_repo)
        solar = _make_solar_supply()
        run_input = _make_run_input(fail_on_empty_weather=True)

        result = await builder.run(run_input, supplies=[solar], demands=[], network_components=[])
        assert result.status == "optimized"

    @pytest.mark.asyncio
    async def test_raises_with_multiple_generators(self) -> None:
        """Error message should list all affected generators."""
        pv_repo = AsyncMock()
        pv_repo.get_solar_profile.return_value = [0.0] * 24
        pv_repo.get_wind_profile.return_value = [0.0] * 24

        builder = PyPSANetworkBuilder(pv_profile_repo=pv_repo)
        solar = _make_solar_supply("Solar Farm A")
        wind = _make_wind_supply("Wind Farm B")
        run_input = _make_run_input(fail_on_empty_weather=True)

        with pytest.raises(WeatherDataEmptyError) as exc_info:
            await builder.run(run_input, supplies=[solar, wind], demands=[], network_components=[])

        assert "Solar Farm A" in exc_info.value.generator_names
        assert "Wind Farm B" in exc_info.value.generator_names


class TestSimulationRunInputDefault:
    """Tests for the fail_on_empty_weather field default."""

    def test_default_is_true(self) -> None:
        run_input = SimulationRunInput()
        assert run_input.fail_on_empty_weather is True

    def test_can_set_to_false(self) -> None:
        run_input = SimulationRunInput(fail_on_empty_weather=False)
        assert run_input.fail_on_empty_weather is False
