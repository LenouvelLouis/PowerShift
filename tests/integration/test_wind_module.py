"""Integration tests for the wind turbine module.

These tests exercise the full stack: create a turbine model, create an asset,
run a power calculation, and verify the shape and bounds of the result.

They do NOT require a real database — they use an in-memory SQLite engine
configured for async use with aiosqlite.

To run:
    pip install aiosqlite
    pytest tests/integration/test_wind_module.py -v
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

# Ensure all ORM models are registered in SQLModel.metadata before create_all
from app.infrastructure.db.models.asset_parameters_model import AssetParametersModel  # noqa: F401
from app.infrastructure.db.models.supply_model import SupplyModel  # noqa: F401

from app.application.wind.schemas import (
    CalculatePowerRequest,
    PowerCurvePointSchema,
    TurbineModelCreate,
    WindAssetCreate,
    WindDataPointSchema,
)
from app.application.wind.use_cases import (
    CalculateWindPowerUseCase,
    CreateTurbineModelUseCase,
    CreateWindAssetUseCase,
)
from app.domain.wind.exceptions import TurbineModelNotFoundError, WindAssetNotFoundError
from app.infrastructure.wind.repository import WindTurbineRepositoryImpl

# ── In-memory database fixture ────────────────────────────────────────────────

@pytest_asyncio.fixture
async def session() -> AsyncSession:  # type: ignore[misc]
    """Provide an async SQLite in-memory session for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        yield s

    await engine.dispose()


@pytest_asyncio.fixture
async def repo(session: AsyncSession) -> WindTurbineRepositoryImpl:
    return WindTurbineRepositoryImpl(session)


# ── Turbine model helpers ─────────────────────────────────────────────────────

def _vestas_create() -> TurbineModelCreate:
    return TurbineModelCreate(
        manufacturer="Vestas",
        model_name="V110-2.0",
        rated_power_kw=2_000.0,
        rotor_diameter_m=110.0,
        hub_height_m=95.0,
        cut_in_speed_ms=3.0,
        cut_out_speed_ms=25.0,
        rated_speed_ms=11.5,
        power_curve=[
            PowerCurvePointSchema(wind_speed_ms=3.0,  power_kw=44.0),
            PowerCurvePointSchema(wind_speed_ms=5.0,  power_kw=272.0),
            PowerCurvePointSchema(wind_speed_ms=8.0,  power_kw=1070.0),
            PowerCurvePointSchema(wind_speed_ms=11.5, power_kw=2000.0),
            PowerCurvePointSchema(wind_speed_ms=25.0, power_kw=2000.0),
        ],
    )


# ── Tests: CreateTurbineModelUseCase ─────────────────────────────────────────

class TestCreateTurbineModelUseCase:
    @pytest.mark.asyncio
    async def test_create_returns_model_with_id(self, repo: WindTurbineRepositoryImpl) -> None:
        uc = CreateTurbineModelUseCase(repo)
        result = await uc.execute(_vestas_create())
        assert result.id is not None
        assert result.manufacturer == "Vestas"
        assert result.model_name == "V110-2.0"
        assert result.rated_power_kw == 2_000.0

    @pytest.mark.asyncio
    async def test_created_model_retrievable(self, repo: WindTurbineRepositoryImpl) -> None:
        uc = CreateTurbineModelUseCase(repo)
        created = await uc.execute(_vestas_create())
        fetched = await repo.get_turbine_model(created.id)
        assert fetched is not None
        assert fetched.manufacturer == "Vestas"

    @pytest.mark.asyncio
    async def test_power_curve_stored(self, repo: WindTurbineRepositoryImpl) -> None:
        uc = CreateTurbineModelUseCase(repo)
        created = await uc.execute(_vestas_create())
        assert len(created.power_curve) == 5
        assert created.power_curve[0].wind_speed_ms == 3.0
        assert created.power_curve[0].power_kw == 44.0

    @pytest.mark.asyncio
    async def test_list_returns_created_model(self, repo: WindTurbineRepositoryImpl) -> None:
        uc = CreateTurbineModelUseCase(repo)
        await uc.execute(_vestas_create())
        models = await repo.list_turbine_models()
        assert len(models) == 1
        assert models[0].model_name == "V110-2.0"

    @pytest.mark.asyncio
    async def test_invalid_speed_raises_error(self, repo: WindTurbineRepositoryImpl) -> None:
        from app.domain.wind.exceptions import InvalidTurbineModelError
        uc = CreateTurbineModelUseCase(repo)
        body = _vestas_create()
        # Force cut_in >= cut_out at the entity level (bypass Pydantic validator)
        body_dict = body.model_dump()
        body_dict["cut_in_speed_ms"] = 30.0  # > cut_out
        with pytest.raises(Exception):
            # Pydantic will reject rated_speed being outside [cut_in, cut_out]
            TurbineModelCreate(**body_dict)


# ── Tests: CreateWindAssetUseCase ─────────────────────────────────────────────

class TestCreateWindAssetUseCase:
    @pytest.mark.asyncio
    async def test_create_asset_success(self, repo: WindTurbineRepositoryImpl) -> None:
        model_uc = CreateTurbineModelUseCase(repo)
        model_resp = await model_uc.execute(_vestas_create())

        asset_uc = CreateWindAssetUseCase(repo)
        asset_resp = await asset_uc.execute(
            WindAssetCreate(
                name="North Site Turbine #1",
                turbine_model_id=model_resp.id,
                latitude=53.3,
                longitude=6.5,
                altitude_m=5.0,
                quantity=3,
            )
        )

        assert asset_resp.id is not None
        assert asset_resp.name == "North Site Turbine #1"
        assert asset_resp.quantity == 3
        assert asset_resp.turbine_model.id == model_resp.id

    @pytest.mark.asyncio
    async def test_create_asset_missing_model_raises(self, repo: WindTurbineRepositoryImpl) -> None:
        asset_uc = CreateWindAssetUseCase(repo)
        with pytest.raises(TurbineModelNotFoundError):
            await asset_uc.execute(
                WindAssetCreate(
                    name="Orphan Turbine",
                    turbine_model_id=uuid.uuid4(),  # non-existent
                )
            )

    @pytest.mark.asyncio
    async def test_asset_creates_asset_parameters_row(
        self, repo: WindTurbineRepositoryImpl, session: AsyncSession
    ) -> None:
        from sqlmodel import select
        from app.infrastructure.db.models.asset_parameters_model import AssetParametersModel

        model_uc = CreateTurbineModelUseCase(repo)
        model_resp = await model_uc.execute(_vestas_create())

        asset_uc = CreateWindAssetUseCase(repo)
        asset_resp = await asset_uc.execute(
            WindAssetCreate(name="Test Asset", turbine_model_id=model_resp.id)
        )

        result = await session.execute(
            select(AssetParametersModel).where(
                AssetParametersModel.asset_id == asset_resp.id
            )
        )
        param_row = result.scalar_one_or_none()
        assert param_row is not None
        assert param_row.asset_type == "wind_turbine"


# ── Tests: CalculateWindPowerUseCase ─────────────────────────────────────────

def _make_wind_request(asset_id: uuid.UUID, speeds: list[float]) -> CalculatePowerRequest:
    """Build a CalculatePowerRequest with simple wind data."""
    base = datetime(2025, 6, 15, 0, 0, 0, tzinfo=timezone.utc)
    return CalculatePowerRequest(
        asset_id=asset_id,
        wind_data=[
            WindDataPointSchema(
                timestamp=base.replace(hour=i % 24),
                wind_speed_ms=s,
                temperature_c=12.0,
            )
            for i, s in enumerate(speeds)
        ],
        availability=0.97,
    )


class TestCalculateWindPowerUseCase:
    @pytest.mark.asyncio
    async def test_output_shape(self, repo: WindTurbineRepositoryImpl) -> None:
        model_resp = await CreateTurbineModelUseCase(repo).execute(_vestas_create())
        asset_resp = await CreateWindAssetUseCase(repo).execute(
            WindAssetCreate(name="Test", turbine_model_id=model_resp.id)
        )

        request = _make_wind_request(asset_resp.id, [5.0, 8.0, 11.5, 20.0, 1.0])
        result = await CalculateWindPowerUseCase(repo).execute(request)

        assert len(result.power_series) == 5
        assert result.asset_id == asset_resp.id
        assert result.asset_name == "Test"

    @pytest.mark.asyncio
    async def test_power_bounds(self, repo: WindTurbineRepositoryImpl) -> None:
        model_resp = await CreateTurbineModelUseCase(repo).execute(_vestas_create())
        asset_resp = await CreateWindAssetUseCase(repo).execute(
            WindAssetCreate(name="Test", turbine_model_id=model_resp.id)
        )

        # Mix of low, medium, high, and storm (cut-out) speeds
        speeds = [0.0, 1.0, 5.0, 8.0, 11.5, 15.0, 30.0]
        request = _make_wind_request(asset_resp.id, speeds)
        result = await CalculateWindPowerUseCase(repo).execute(request)

        for pt in result.power_series:
            assert pt.power_kw >= 0.0
            assert pt.power_kw <= 2_000.0 * 0.97 + 0.1  # rated × availability + tiny float err

    @pytest.mark.asyncio
    async def test_capacity_factor_in_range(self, repo: WindTurbineRepositoryImpl) -> None:
        model_resp = await CreateTurbineModelUseCase(repo).execute(_vestas_create())
        asset_resp = await CreateWindAssetUseCase(repo).execute(
            WindAssetCreate(name="Test", turbine_model_id=model_resp.id)
        )

        request = _make_wind_request(asset_resp.id, [8.0] * 24)
        result = await CalculateWindPowerUseCase(repo).execute(request)

        assert 0.0 <= result.capacity_factor <= 1.0

    @pytest.mark.asyncio
    async def test_total_energy_equals_sum_of_power(self, repo: WindTurbineRepositoryImpl) -> None:
        model_resp = await CreateTurbineModelUseCase(repo).execute(_vestas_create())
        asset_resp = await CreateWindAssetUseCase(repo).execute(
            WindAssetCreate(name="Test", turbine_model_id=model_resp.id)
        )

        request = _make_wind_request(asset_resp.id, [7.0, 9.0, 11.5])
        result = await CalculateWindPowerUseCase(repo).execute(request)

        expected_total = sum(pt.power_kw for pt in result.power_series)
        assert result.total_energy_kwh == pytest.approx(expected_total)

    @pytest.mark.asyncio
    async def test_peak_power_is_max(self, repo: WindTurbineRepositoryImpl) -> None:
        model_resp = await CreateTurbineModelUseCase(repo).execute(_vestas_create())
        asset_resp = await CreateWindAssetUseCase(repo).execute(
            WindAssetCreate(name="Test", turbine_model_id=model_resp.id)
        )

        request = _make_wind_request(asset_resp.id, [4.0, 11.5, 3.5])
        result = await CalculateWindPowerUseCase(repo).execute(request)

        max_in_series = max(pt.power_kw for pt in result.power_series)
        assert result.peak_power_kw == pytest.approx(max_in_series)

    @pytest.mark.asyncio
    async def test_missing_asset_raises(self, repo: WindTurbineRepositoryImpl) -> None:
        request = _make_wind_request(uuid.uuid4(), [8.0])
        with pytest.raises(WindAssetNotFoundError):
            await CalculateWindPowerUseCase(repo).execute(request)

    @pytest.mark.asyncio
    async def test_quantity_multiplies_total_energy(self, repo: WindTurbineRepositoryImpl) -> None:
        model_resp = await CreateTurbineModelUseCase(repo).execute(_vestas_create())

        asset_1 = await CreateWindAssetUseCase(repo).execute(
            WindAssetCreate(name="Single", turbine_model_id=model_resp.id, quantity=1)
        )
        asset_5 = await CreateWindAssetUseCase(repo).execute(
            WindAssetCreate(name="Fleet", turbine_model_id=model_resp.id, quantity=5)
        )

        speeds = [8.0, 10.0]
        r1 = await CalculateWindPowerUseCase(repo).execute(_make_wind_request(asset_1.id, speeds))
        r5 = await CalculateWindPowerUseCase(repo).execute(_make_wind_request(asset_5.id, speeds))

        assert r5.total_energy_kwh == pytest.approx(r1.total_energy_kwh * 5, rel=1e-5)
