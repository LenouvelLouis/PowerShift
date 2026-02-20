import pytest
from fastapi.testclient import TestClient

from app.main import app


# --------------------------------------------------
# Fixture — shared test client for all tests in this file
# --------------------------------------------------
@pytest.fixture(scope="module")
def client() -> TestClient:
    with TestClient(app) as c:
        yield c


# --------------------------------------------------
# GET /health
# --------------------------------------------------
class TestHealthCheck:
    def test_status_code_is_200(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200

    def test_response_contains_ok_status(self, client: TestClient) -> None:
        data = client.get("/health").json()
        assert data["status"] == "ok"

    def test_response_contains_app_name(self, client: TestClient) -> None:
        data = client.get("/health").json()
        assert "app" in data
        assert isinstance(data["app"], str)

    def test_response_contains_version(self, client: TestClient) -> None:
        data = client.get("/health").json()
        assert "version" in data

    def test_response_contains_environment(self, client: TestClient) -> None:
        data = client.get("/health").json()
        assert "environment" in data
