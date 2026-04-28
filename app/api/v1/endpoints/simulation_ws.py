"""WebSocket endpoint for live simulation preview.

Replaces the polling HTTP POST /preview with a persistent connection.
The client sends SimulationRunRequest JSON messages; the server replies
with SimulationRunResponse JSON (or an error object).

Server-side debounce: if a new message arrives while a simulation is
in flight, the old result is discarded and the new request is executed.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from app.api.v1.schemas.simulation_schema import SimulationRunRequest
from app.application.services.simulation_service import SimulationService
from app.config import settings
from app.domain.simulation.exceptions import WeatherDataEmptyError
from app.domain.use_cases.preview_simulation import PreviewSimulationUseCase
from app.infrastructure.db.connection import get_session_factory
from app.infrastructure.db.repositories.custom_profile_repository_impl import CustomProfileRepositoryImpl
from app.infrastructure.db.repositories.demand_repository_impl import DemandRepositoryImpl
from app.infrastructure.db.repositories.network_repository_impl import NetworkRepositoryImpl
from app.infrastructure.db.repositories.supply_repository_impl import SupplyRepositoryImpl
from app.infrastructure.db.repositories.weather_profile_repository_impl import WeatherProfileRepositoryImpl
from app.infrastructure.external.open_meteo_provider import OpenMeteoLoadProfileProvider
from app.infrastructure.simulation.network_builder import PyPSANetworkBuilder

_log = logging.getLogger("app.ws.simulation")

# Server-side debounce delay in seconds.
_DEBOUNCE_SECONDS = 0.2


def _build_preview_service_from_session(session) -> SimulationService:  # noqa: ANN001
    """Build a SimulationService wired for preview-only (no persistence writes)."""
    supply_repo = SupplyRepositoryImpl(session)
    demand_repo = DemandRepositoryImpl(session)
    network_repo = NetworkRepositoryImpl(session)
    pv_repo = WeatherProfileRepositoryImpl(session)

    preview_uc = PreviewSimulationUseCase(
        grid_simulation=PyPSANetworkBuilder(
            load_profile_provider=OpenMeteoLoadProfileProvider(),
            pv_profile_repo=pv_repo,
        ),
        supply_repo=supply_repo,
        demand_repo=demand_repo,
        network_repo=network_repo,
    )
    custom_profile_repo = CustomProfileRepositoryImpl(session)
    return SimulationService(
        use_case=None,  # type: ignore[arg-type]  # not used for preview
        persistence=None,  # type: ignore[arg-type]  # not used for preview
        preview_use_case=preview_uc,
        custom_profile_repo=custom_profile_repo,
    )


async def _authenticate_ws(websocket: WebSocket) -> bool:
    """Check API key on WebSocket connection if authentication is enabled.

    The key can be sent as a query parameter ``api_key`` or as the first
    element of the Sec-WebSocket-Protocol subprotocol list (for browser
    clients that cannot set custom headers on WS connections).
    """
    expected = settings.API_KEY
    if not expected:
        return True

    # Try query parameter first
    provided = websocket.query_params.get("api_key")
    if provided and provided == expected:
        return True

    # Try X-API-Key header (works from non-browser clients)
    provided = websocket.headers.get("x-api-key")
    if provided and provided == expected:
        return True

    return False


def _error_msg(message: str, code: str = "ERR_UNKNOWN") -> dict[str, Any]:
    return {"error": message, "code": code}


async def simulation_ws_endpoint(websocket: WebSocket) -> None:
    """WebSocket handler for ``/api/v1/simulation/ws``.

    Protocol:
    - Client sends JSON conforming to SimulationRunRequest.
    - Server replies with SimulationRunResponse JSON or an error object.
    - If a new request arrives while the previous simulation is still
      running, the old task is cancelled and the new one takes over.
    """
    if not await _authenticate_ws(websocket):
        await websocket.close(code=4401, reason="Invalid or missing API key")
        return

    await websocket.accept()
    _log.info("WebSocket simulation client connected")

    current_task: asyncio.Task | None = None

    try:
        while True:
            raw = await websocket.receive_text()

            # ── Parse request ───────────────────────────────────────────
            try:
                body = SimulationRunRequest.model_validate_json(raw)
            except ValidationError as exc:
                await websocket.send_json(_error_msg(str(exc), "ERR_VALIDATION"))
                continue

            # ── Cancel previous in-flight simulation ────────────────────
            if current_task is not None and not current_task.done():
                current_task.cancel()
                try:
                    await current_task
                except (asyncio.CancelledError, Exception):
                    pass

            # ── Schedule new simulation with debounce ───────────────────
            current_task = asyncio.create_task(_debounced_preview(websocket, body))

    except WebSocketDisconnect:
        _log.info("WebSocket simulation client disconnected")
    except Exception:
        _log.exception("Unexpected error in simulation WebSocket")
    finally:
        if current_task is not None and not current_task.done():
            current_task.cancel()


async def _debounced_preview(websocket: WebSocket, body: SimulationRunRequest) -> None:
    """Wait for the debounce window, then run the preview simulation.

    If this task is cancelled during the debounce wait (because a newer
    request arrived), it exits silently.
    """
    await asyncio.sleep(_DEBOUNCE_SECONDS)

    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            service = _build_preview_service_from_session(session)
            result = await service.preview(body)
            await websocket.send_json(result.model_dump(mode="json"))
        except WeatherDataEmptyError as exc:
            await websocket.send_json(_error_msg(str(exc), "ERR_WEATHER_DATA_EMPTY"))
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            _log.exception("Simulation preview failed via WebSocket")
            await websocket.send_json(_error_msg(str(exc), "ERR_SIMULATION_FAILED"))
