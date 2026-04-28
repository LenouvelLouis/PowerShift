"""API tests for custom hourly load profile sub-resource on /api/v1/demands/{id}/profile."""

from __future__ import annotations

import io
import uuid

from fastapi.testclient import TestClient


def _create_demand(client: TestClient, name: str = "Profile Test House") -> str:
    """Helper: create a demand and return its UUID string."""
    payload = {"name": name, "type": "house", "load_mw": 5.0}
    resp = client.post("/api/v1/demands", json=payload)
    assert resp.status_code == 201
    return resp.json()["id"]


def _make_csv(hours: int = 24, *, bad_factor: float | None = None, duplicate_hour: int | None = None) -> bytes:
    """Build a valid (or intentionally invalid) CSV payload."""
    lines = ["hour,load_factor"]
    for h in range(hours):
        factor = bad_factor if bad_factor is not None else round(h / max(hours - 1, 1), 4)
        lines.append(f"{h},{factor}")
    if duplicate_hour is not None:
        lines.append(f"{duplicate_hour},0.5")
    return "\n".join(lines).encode()


# ── Upload ──────────────────────────────────────────────────────────────────


class TestUploadProfile:
    def test_upload_24h_csv(self, client: TestClient) -> None:
        demand_id = _create_demand(client)
        csv_bytes = _make_csv(24)
        resp = client.post(
            f"/api/v1/demands/{demand_id}/profile",
            files={"file": ("profile.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["demand_id"] == demand_id
        assert len(data["profile_data"]) == 24
        assert all(0.0 <= v <= 1.0 for v in data["profile_data"])

    def test_upload_replaces_existing(self, client: TestClient) -> None:
        demand_id = _create_demand(client, "Replace Test")
        csv1 = _make_csv(24)
        client.post(
            f"/api/v1/demands/{demand_id}/profile",
            files={"file": ("p.csv", io.BytesIO(csv1), "text/csv")},
        )
        # Upload a second time — should replace (upsert)
        csv2 = _make_csv(24)
        resp = client.post(
            f"/api/v1/demands/{demand_id}/profile",
            files={"file": ("p2.csv", io.BytesIO(csv2), "text/csv")},
        )
        assert resp.status_code == 201

    def test_upload_demand_not_found(self, client: TestClient) -> None:
        fake_id = str(uuid.uuid4())
        csv_bytes = _make_csv(24)
        resp = client.post(
            f"/api/v1/demands/{fake_id}/profile",
            files={"file": ("p.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        assert resp.status_code == 404

    def test_upload_invalid_length(self, client: TestClient) -> None:
        demand_id = _create_demand(client, "Bad Length")
        csv_bytes = _make_csv(10)  # 10 rows — not in {24, 168, 8760}
        resp = client.post(
            f"/api/v1/demands/{demand_id}/profile",
            files={"file": ("p.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        assert resp.status_code == 422

    def test_upload_factor_out_of_range(self, client: TestClient) -> None:
        demand_id = _create_demand(client, "Bad Factor")
        csv_bytes = _make_csv(24, bad_factor=1.5)
        resp = client.post(
            f"/api/v1/demands/{demand_id}/profile",
            files={"file": ("p.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        assert resp.status_code == 422

    def test_upload_duplicate_hour(self, client: TestClient) -> None:
        demand_id = _create_demand(client, "Dup Hour")
        csv_bytes = _make_csv(24, duplicate_hour=5)
        resp = client.post(
            f"/api/v1/demands/{demand_id}/profile",
            files={"file": ("p.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        assert resp.status_code == 422

    def test_upload_missing_columns(self, client: TestClient) -> None:
        demand_id = _create_demand(client, "Missing Col")
        bad_csv = b"hour,wrong_col\n0,0.5\n"
        resp = client.post(
            f"/api/v1/demands/{demand_id}/profile",
            files={"file": ("p.csv", io.BytesIO(bad_csv), "text/csv")},
        )
        assert resp.status_code == 422


# ── Get ─────────────────────────────────────────────────────────────────────


class TestGetProfile:
    def test_get_existing_profile(self, client: TestClient) -> None:
        demand_id = _create_demand(client, "Get Test")
        csv_bytes = _make_csv(24)
        client.post(
            f"/api/v1/demands/{demand_id}/profile",
            files={"file": ("p.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        resp = client.get(f"/api/v1/demands/{demand_id}/profile")
        assert resp.status_code == 200
        data = resp.json()
        assert data["demand_id"] == demand_id
        assert len(data["profile_data"]) == 24

    def test_get_no_profile_returns_null(self, client: TestClient) -> None:
        demand_id = _create_demand(client, "No Profile")
        resp = client.get(f"/api/v1/demands/{demand_id}/profile")
        assert resp.status_code == 200
        assert resp.json() is None

    def test_get_demand_not_found(self, client: TestClient) -> None:
        fake_id = str(uuid.uuid4())
        resp = client.get(f"/api/v1/demands/{fake_id}/profile")
        assert resp.status_code == 404


# ── Delete ──────────────────────────────────────────────────────────────────


class TestDeleteProfile:
    def test_delete_existing_profile(self, client: TestClient) -> None:
        demand_id = _create_demand(client, "Del Test")
        csv_bytes = _make_csv(24)
        client.post(
            f"/api/v1/demands/{demand_id}/profile",
            files={"file": ("p.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        resp = client.delete(f"/api/v1/demands/{demand_id}/profile")
        assert resp.status_code == 204

        # Verify it's gone
        resp = client.get(f"/api/v1/demands/{demand_id}/profile")
        assert resp.status_code == 200
        assert resp.json() is None

    def test_delete_nonexistent_profile_is_idempotent(self, client: TestClient) -> None:
        demand_id = _create_demand(client, "Del Noop")
        resp = client.delete(f"/api/v1/demands/{demand_id}/profile")
        assert resp.status_code == 204

    def test_delete_demand_not_found(self, client: TestClient) -> None:
        fake_id = str(uuid.uuid4())
        resp = client.delete(f"/api/v1/demands/{fake_id}/profile")
        assert resp.status_code == 404
