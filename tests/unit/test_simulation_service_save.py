"""Unit tests for SimulationService.save()."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.api.v1.schemas.simulation_schema import SimulationRunRequest, SimulationRunResponse
from app.application.services.simulation_service import SimulationService
from app.domain.interfaces.simulation_repository import SimulationRunInput, SimulationRunOutput


def _make_request() -> SimulationRunRequest:
    return SimulationRunRequest(
        supply_ids=["s1"],
        demand_ids=["d1"],
        network_ids=[],
        snapshot_hours=24,
        solver="highs",
        optimization_objective="min_cost",
        start_date="2025-06-01",
        end_date="2025-06-01",
    )


def _make_output() -> SimulationRunOutput:
    return SimulationRunOutput(
        total_supply_mwh=100.0,
        total_demand_mwh=90.0,
        balance_mwh=10.0,
        status="optimal",
        objective_value=42.0,
        result_json={"generators_t": {}},
    )


def _make_result_row(request_id: uuid.UUID) -> MagicMock:
    row = MagicMock()
    row.id = uuid.uuid4()
    row.request_id = request_id
    row.status = "optimal"
    row.total_supply_mwh = 100.0
    row.total_demand_mwh = 90.0
    row.balance_mwh = 10.0
    row.objective_value = 42.0
    row.result_json = {"generators_t": {}}
    row.created_at = datetime.now(timezone.utc)
    return row


def _make_req_row(request_id: uuid.UUID) -> MagicMock:
    req = MagicMock()
    req.id = request_id
    req.solver = "highs"
    req.name = None
    req.start_date = None
    req.end_date = None
    return req


@pytest.fixture
def service():
    use_case = AsyncMock()
    persistence = AsyncMock()
    preview_use_case = AsyncMock()
    return SimulationService(
        use_case=use_case,
        persistence=persistence,
        preview_use_case=preview_use_case,
    )


class TestSimulationServiceSave:
    @pytest.mark.asyncio
    async def test_save_calls_preview_use_case(self, service):
        output = _make_output()
        request_id = uuid.uuid4()
        result_row = _make_result_row(request_id)
        req_row = _make_req_row(request_id)

        service._preview_use_case.execute.return_value = output
        service._persistence.save_request.return_value = request_id
        service._persistence.save_result.return_value = result_row
        service._persistence.get_result_by_id.return_value = result_row
        service._persistence.get_request_by_id.return_value = req_row

        body = _make_request()
        await service.save(body)

        service._preview_use_case.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_does_not_call_run_use_case(self, service):
        output = _make_output()
        request_id = uuid.uuid4()
        result_row = _make_result_row(request_id)
        req_row = _make_req_row(request_id)

        service._preview_use_case.execute.return_value = output
        service._persistence.save_request.return_value = request_id
        service._persistence.save_result.return_value = result_row
        service._persistence.get_result_by_id.return_value = result_row
        service._persistence.get_request_by_id.return_value = req_row

        await service.save(_make_request())

        service._use_case.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_save_persists_request_and_result(self, service):
        output = _make_output()
        request_id = uuid.uuid4()
        result_row = _make_result_row(request_id)
        req_row = _make_req_row(request_id)

        service._preview_use_case.execute.return_value = output
        service._persistence.save_request.return_value = request_id
        service._persistence.save_result.return_value = result_row
        service._persistence.get_result_by_id.return_value = result_row
        service._persistence.get_request_by_id.return_value = req_row

        await service.save(_make_request())

        service._persistence.save_request.assert_called_once()
        service._persistence.save_result.assert_called_once_with(request_id, output)

    @pytest.mark.asyncio
    async def test_save_returns_simulation_run_response(self, service):
        output = _make_output()
        request_id = uuid.uuid4()
        result_row = _make_result_row(request_id)
        req_row = _make_req_row(request_id)

        service._preview_use_case.execute.return_value = output
        service._persistence.save_request.return_value = request_id
        service._persistence.save_result.return_value = result_row
        service._persistence.get_result_by_id.return_value = result_row
        service._persistence.get_request_by_id.return_value = req_row

        result = await service.save(_make_request())

        assert isinstance(result, SimulationRunResponse)
        assert result.status == "optimal"
        assert result.total_supply_mwh == 100.0

    @pytest.mark.asyncio
    async def test_save_raises_if_preview_use_case_not_wired(self):
        use_case = AsyncMock()
        persistence = AsyncMock()
        service = SimulationService(use_case=use_case, persistence=persistence, preview_use_case=None)

        with pytest.raises(RuntimeError, match="PreviewSimulationUseCase not wired"):
            await service.save(_make_request())
