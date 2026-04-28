"""Integration tests for the X-Request-ID middleware."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.main import app


class TestRequestIdMiddleware:
    """Verify request_id generation and pass-through."""

    def setup_method(self) -> None:
        self.client = TestClient(app)

    def test_response_contains_x_request_id_header(self) -> None:
        resp = self.client.get("/health")
        rid = resp.headers.get("X-Request-ID")
        assert rid is not None
        # Must be a valid UUID4 when auto-generated
        uuid.UUID(rid, version=4)

    def test_echoes_provided_request_id(self) -> None:
        custom_rid = "my-trace-id-42"
        resp = self.client.get("/health", headers={"X-Request-ID": custom_rid})
        assert resp.headers["X-Request-ID"] == custom_rid

    def test_different_requests_get_different_ids(self) -> None:
        r1 = self.client.get("/health")
        r2 = self.client.get("/health")
        assert r1.headers["X-Request-ID"] != r2.headers["X-Request-ID"]
