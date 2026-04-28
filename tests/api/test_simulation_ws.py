"""Tests for the WebSocket simulation preview endpoint ``/api/v1/simulation/ws``."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def ws_client(client: TestClient) -> TestClient:
    """Return the shared TestClient (which supports ``with client.websocket_connect(...):``)."""
    return client


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VALID_REQUEST = {
    "snapshot_hours": 24,
    "solver": "highs",
    "supply_ids": [],
    "demand_ids": [],
    "network_ids": [],
    "start_date": "2025-06-01",
    "end_date": "2025-06-01",
}

_MOCK_PREVIEW_RESPONSE = {
    "id": "00000000-0000-0000-0000-000000000001",
    "request_id": "00000000-0000-0000-0000-000000000002",
    "status": "optimal",
    "solver": "highs",
    "total_supply_mwh": 10.0,
    "total_demand_mwh": 8.0,
    "balance_mwh": 2.0,
    "objective_value": 100.0,
    "result_json": {"generators_t": {}},
    "created_at": "2025-06-01T00:00:00",
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSimulationWebSocket:
    """WebSocket endpoint tests using Starlette TestClient."""

    def test_connect_and_receive_result(self, ws_client: TestClient) -> None:
        """Client sends a valid request and receives a simulation result."""
        import uuid
        from datetime import UTC, datetime

        from app.api.v1.schemas.simulation_schema import SimulationRunResponse

        mock_response = SimulationRunResponse(
            id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            request_id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
            status="optimal",
            solver="highs",
            total_supply_mwh=10.0,
            total_demand_mwh=8.0,
            balance_mwh=2.0,
            objective_value=100.0,
            result_json={"generators_t": {}},
            created_at=datetime(2025, 6, 1, tzinfo=UTC),
        )

        with patch(
            "app.api.v1.endpoints.simulation_ws._debounced_preview",
            new_callable=AsyncMock,
        ) as mock_preview:
            # Instead of running the real preview, send back a canned response
            async def fake_preview(websocket, body):  # noqa: ANN001, ARG001
                await websocket.send_json(mock_response.model_dump(mode="json"))

            mock_preview.side_effect = fake_preview

            with ws_client.websocket_connect("/api/v1/simulation/ws") as ws:
                ws.send_text(json.dumps(_VALID_REQUEST))
                data = ws.receive_json()
                assert data["status"] == "optimal"
                assert data["total_supply_mwh"] == 10.0

    def test_invalid_json_returns_error(self, ws_client: TestClient) -> None:
        """Sending invalid JSON returns a validation error."""
        with patch(
            "app.api.v1.endpoints.simulation_ws._debounced_preview",
            new_callable=AsyncMock,
        ):
            with ws_client.websocket_connect("/api/v1/simulation/ws") as ws:
                ws.send_text('{"snapshot_hours": -5}')
                data = ws.receive_json()
                assert "error" in data
                assert data["code"] == "ERR_VALIDATION"

    def test_auth_rejected_when_key_set(self, ws_client: TestClient) -> None:
        """When API_KEY is set, connections without the key are rejected."""
        with patch("app.api.v1.endpoints.simulation_ws.settings") as mock_settings:
            mock_settings.API_KEY = "test-secret-key"

            # Connection without key should be closed with 4401
            with pytest.raises(Exception):
                with ws_client.websocket_connect("/api/v1/simulation/ws") as ws:
                    ws.receive_json()

    def test_auth_accepted_with_query_param(self, ws_client: TestClient) -> None:
        """When API_KEY is set, connections with the correct query param succeed."""
        with patch("app.api.v1.endpoints.simulation_ws.settings") as mock_settings:
            mock_settings.API_KEY = "test-secret-key"

            with patch(
                "app.api.v1.endpoints.simulation_ws._debounced_preview",
                new_callable=AsyncMock,
            ):
                with ws_client.websocket_connect(
                    "/api/v1/simulation/ws?api_key=test-secret-key"
                ) as ws:
                    ws.send_text(json.dumps(_VALID_REQUEST))
                    data = ws.receive_json()
                    # Should get a validation error or result, not an auth error
                    assert "error" in data or "status" in data
