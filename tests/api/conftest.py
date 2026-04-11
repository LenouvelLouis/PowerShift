"""Shared fixtures for API-level integration tests.

These tests run against a local SQLite database to avoid relying on
external network/database availability during local test runs.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel

# Use a local file DB for API tests.
TEST_DB_PATH = Path("test_api.db")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB_PATH}"
os.environ["ENVIRONMENT"] = "testing"

# Ensure cached settings/engine are rebuilt from the test DATABASE_URL.
from app.infrastructure.secrets.settings import get_settings

get_settings.cache_clear()

from app.infrastructure.db import connection as db_connection

db_connection._engine = None
db_connection._session_factory = None

# Import model modules so SQLModel metadata is fully registered.
from app.infrastructure.db.models import (  # noqa: F401
    asset_parameters_model,
    demand_model,
    network_model,
    simulation_request_model,
    simulation_result_model,
    supply_model,
    weather_profile_model,
)
from app.main import app


async def _prepare_db() -> None:
    engine = db_connection.get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)


def _run_async(coro: object) -> None:
    """Run a coroutine in the current event loop or create one."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    
    if loop is None:
        asyncio.run(coro)  # type: ignore[arg-type]
    else:
        # If we're already in a loop, we can't use asyncio.run()
        # This shouldn't happen in conftest session scope, but just in case
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, coro)  # type: ignore[arg-type]
            future.result()


@pytest.fixture(scope="session", autouse=True)
def setup_test_db() -> None:
    """Initialize test database before running tests."""
    _run_async(_prepare_db())
    yield
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest.fixture(scope="session")
def client(setup_test_db: None) -> TestClient:  # noqa: ARG001
    """Provide a TestClient for API tests."""
    with TestClient(app) as c:
        yield c
