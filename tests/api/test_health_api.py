"""API tests for the /health endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestHealthEndpoint:
    def test_returns_200(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200

    def test_status_field_is_ok(self, client: TestClient):
        data = client.get("/health").json()
        assert data["status"] == "ok"

    def test_contains_app_metadata(self, client: TestClient):
        data = client.get("/health").json()
        assert "app" in data
        assert "version" in data
        assert "environment" in data
