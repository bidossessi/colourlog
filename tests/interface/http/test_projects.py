# SPDX-License-Identifier: GPL-3.0-or-later
from typing import cast
from uuid import uuid4

from fastapi.testclient import TestClient


def _make_client(client: TestClient, name: str = "EMSA") -> str:
    return cast("str", client.post("/api/v1/clients", json={"name": name}).json()["id"])


class TestProjectsAPI:
    def test_create_without_client(self, client: TestClient):
        r = client.post("/api/v1/projects", json={"name": "Evvue"})
        assert r.status_code == 201
        assert r.json()["client_id"] is None

    def test_create_with_existing_client(self, client: TestClient):
        cid = _make_client(client)
        r = client.post("/api/v1/projects", json={"name": "Evvue", "client_id": cid})
        assert r.status_code == 201
        assert r.json()["client_id"] == cid

    def test_create_unknown_client_returns_404(self, client: TestClient):
        r = client.post("/api/v1/projects", json={"name": "Evvue", "client_id": str(uuid4())})
        assert r.status_code == 404
        assert r.json()["error"]["code"] == "client_not_found"

    def test_list_filter_by_client(self, client: TestClient):
        c1 = _make_client(client, "C1")
        c2 = _make_client(client, "C2")
        client.post("/api/v1/projects", json={"name": "P1", "client_id": c1})
        client.post("/api/v1/projects", json={"name": "P2", "client_id": c2})
        r = client.get(f"/api/v1/projects?client_id={c1}")
        names = [p["name"] for p in r.json()]
        assert names == ["P1"]

    def test_list_include_archived(self, client: TestClient):
        a = client.post("/api/v1/projects", json={"name": "A"}).json()
        client.post("/api/v1/projects", json={"name": "B"})
        client.patch(f"/api/v1/projects/{a['id']}", json={"archived": True})
        r = client.get("/api/v1/projects?include_archived=true")
        assert len(r.json()) == 2

    def test_get_returns_project(self, client: TestClient):
        created = client.post("/api/v1/projects", json={"name": "Evvue"}).json()
        r = client.get(f"/api/v1/projects/{created['id']}")
        assert r.status_code == 200
        assert r.json() == created

    def test_get_missing_returns_404(self, client: TestClient):
        r = client.get(f"/api/v1/projects/{uuid4()}")
        assert r.status_code == 404

    def test_patch_clear_client(self, client: TestClient):
        cid = _make_client(client)
        p = client.post("/api/v1/projects", json={"name": "Evvue", "client_id": cid}).json()
        r = client.patch(f"/api/v1/projects/{p['id']}", json={"clear_client": True})
        assert r.status_code == 200
        assert r.json()["client_id"] is None

    def test_patch_unknown_new_client_returns_404(self, client: TestClient):
        p = client.post("/api/v1/projects", json={"name": "Evvue"}).json()
        r = client.patch(f"/api/v1/projects/{p['id']}", json={"client_id": str(uuid4())})
        assert r.status_code == 404

    def test_delete_returns_204(self, client: TestClient):
        p = client.post("/api/v1/projects", json={"name": "Evvue"}).json()
        r = client.delete(f"/api/v1/projects/{p['id']}")
        assert r.status_code == 204

    def test_delete_missing_returns_404(self, client: TestClient):
        r = client.delete(f"/api/v1/projects/{uuid4()}")
        assert r.status_code == 404
