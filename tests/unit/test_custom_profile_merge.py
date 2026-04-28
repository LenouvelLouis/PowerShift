"""Unit tests for SimulationService._merge_custom_profiles().

Verifies that DB-stored custom load profiles are injected into
hourly_load_overrides, and that user-supplied overrides take precedence.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.application.services.simulation_service import SimulationService
from app.domain.interfaces.simulation_repository import SimulationRunInput


def _build_service(
    *,
    db_profiles: dict[str, list[float]] | None = None,
) -> SimulationService:
    """Build a SimulationService with a mocked custom_profile_repo."""
    repo = AsyncMock()
    repo.get_all_as_dict = AsyncMock(return_value=db_profiles or {})
    return SimulationService(
        use_case=AsyncMock(),
        persistence=AsyncMock(),
        custom_profile_repo=repo,
    )


@pytest.mark.asyncio
async def test_merge_adds_db_profiles() -> None:
    """DB profiles are added when hourly_load_overrides is empty."""
    profile = [0.5] * 24
    service = _build_service(db_profiles={"demand-uuid-1": profile})

    run_input = SimulationRunInput(demand_ids=["demand-uuid-1"])
    await service._merge_custom_profiles(run_input)

    assert run_input.hourly_load_overrides["demand-uuid-1"] == profile


@pytest.mark.asyncio
async def test_merge_does_not_overwrite_user_override() -> None:
    """User-supplied overrides take precedence over DB profiles."""
    db_profile = [0.3] * 24
    user_profile = [0.9] * 24
    service = _build_service(db_profiles={"demand-uuid-1": db_profile})

    run_input = SimulationRunInput(
        demand_ids=["demand-uuid-1"],
        hourly_load_overrides={"demand-uuid-1": user_profile},
    )
    await service._merge_custom_profiles(run_input)

    assert run_input.hourly_load_overrides["demand-uuid-1"] == user_profile


@pytest.mark.asyncio
async def test_merge_no_repo_is_noop() -> None:
    """When custom_profile_repo is None, nothing happens."""
    service = SimulationService(
        use_case=AsyncMock(),
        persistence=AsyncMock(),
        custom_profile_repo=None,
    )
    run_input = SimulationRunInput()
    await service._merge_custom_profiles(run_input)

    assert run_input.hourly_load_overrides == {}


@pytest.mark.asyncio
async def test_merge_multiple_demands() -> None:
    """Multiple DB profiles are merged; existing user override is preserved."""
    db_profiles = {
        "id-a": [0.1] * 24,
        "id-b": [0.2] * 24,
        "id-c": [0.3] * 24,
    }
    service = _build_service(db_profiles=db_profiles)

    run_input = SimulationRunInput(
        hourly_load_overrides={"id-b": [0.99] * 24},
    )
    await service._merge_custom_profiles(run_input)

    assert run_input.hourly_load_overrides["id-a"] == [0.1] * 24
    assert run_input.hourly_load_overrides["id-b"] == [0.99] * 24  # user wins
    assert run_input.hourly_load_overrides["id-c"] == [0.3] * 24


@pytest.mark.asyncio
async def test_merge_empty_db_profiles() -> None:
    """Empty DB profiles dict leaves overrides unchanged."""
    service = _build_service(db_profiles={})
    run_input = SimulationRunInput(
        hourly_load_overrides={"x": [0.5] * 24},
    )
    await service._merge_custom_profiles(run_input)

    assert run_input.hourly_load_overrides == {"x": [0.5] * 24}
