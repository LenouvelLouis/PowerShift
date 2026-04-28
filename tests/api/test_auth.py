"""Tests for API key authentication."""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient


def test_401_when_api_key_set_and_missing(client: TestClient) -> None:
    """Requests without a key must be rejected when API_KEY is configured."""
    with patch("app.api.v1.auth.settings") as mock_settings:
        mock_settings.API_KEY = "test-secret-key"
        resp = client.get("/api/v1/demands")
    assert resp.status_code == 401
    body = resp.json()
    assert body["detail"] == "Invalid or missing API key"


def test_401_when_api_key_set_and_wrong(client: TestClient) -> None:
    """Requests with a wrong key must be rejected."""
    with patch("app.api.v1.auth.settings") as mock_settings:
        mock_settings.API_KEY = "test-secret-key"
        resp = client.get(
            "/api/v1/demands",
            headers={"X-API-Key": "wrong-key"},
        )
    assert resp.status_code == 401


def test_200_when_api_key_set_and_correct(client: TestClient) -> None:
    """Requests with the correct key must succeed."""
    with patch("app.api.v1.auth.settings") as mock_settings:
        mock_settings.API_KEY = "test-secret-key"
        resp = client.get(
            "/api/v1/demands",
            headers={"X-API-Key": "test-secret-key"},
        )
    assert resp.status_code == 200


def test_200_when_api_key_via_query_param(client: TestClient) -> None:
    """The key can also be passed as a query parameter."""
    with patch("app.api.v1.auth.settings") as mock_settings:
        mock_settings.API_KEY = "test-secret-key"
        resp = client.get("/api/v1/demands", params={"api_key": "test-secret-key"})
    assert resp.status_code == 200


def test_auth_skipped_when_api_key_empty(client: TestClient) -> None:
    """When API_KEY is empty (dev mode), all requests pass without auth."""
    with patch("app.api.v1.auth.settings") as mock_settings:
        mock_settings.API_KEY = ""
        resp = client.get("/api/v1/demands")
    assert resp.status_code == 200


def test_health_endpoint_always_public(client: TestClient) -> None:
    """The /health endpoint must remain accessible without any key."""
    with patch("app.api.v1.auth.settings") as mock_settings:
        mock_settings.API_KEY = "test-secret-key"
        resp = client.get("/health")
    # Health returns 200 or 503 (if DB is down) — never 401
    assert resp.status_code in (200, 503)
