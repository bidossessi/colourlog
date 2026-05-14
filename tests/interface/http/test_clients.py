# SPDX-License-Identifier: GPL-3.0-or-later
from uuid import uuid4

from fastapi.testclient import TestClient


class TestClientsAPI:
    def test_create_returns_201_and_strips_name(self, client: TestClient):
        r = client.post("/api/v1/clients", json={"name": "  EMSA  "})
        assert r.status_code == 201
        body = r.json()
        assert body["name"] == "EMSA"
        assert body["archived"] is False
        assert "id" in body

    def test_create_empty_name_returns_422(self, client: TestClient):
        r = client.post("/api/v1/clients", json={"name": ""})
        assert r.status_code == 422

    def test_create_whitespace_only_name_returns_400_invalid_name(self, client: TestClient):
        r = client.post("/api/v1/clients", json={"name": "   "})
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "invalid_name"

    def test_get_returns_client(self, client: TestClient):
        created = client.post("/api/v1/clients", json={"name": "EMSA"}).json()
        r = client.get(f"/api/v1/clients/{created['id']}")
        assert r.status_code == 200
        assert r.json() == created

    def test_get_missing_returns_404_with_envelope(self, client: TestClient):
        r = client.get(f"/api/v1/clients/{uuid4()}")
        assert r.status_code == 404
        body = r.json()
        assert body["error"]["code"] == "client_not_found"
        assert "id" in body["error"]["details"]

    def test_list_excludes_archived_by_default(self, client: TestClient):
        a = client.post("/api/v1/clients", json={"name": "A"}).json()
        client.post("/api/v1/clients", json={"name": "B"}).json()
        client.patch(f"/api/v1/clients/{a['id']}", json={"archived": True})
        r = client.get("/api/v1/clients")
        names = [c["name"] for c in r.json()]
        assert names == ["B"]

    def test_list_include_archived(self, client: TestClient):
        a = client.post("/api/v1/clients", json={"name": "A"}).json()
        client.post("/api/v1/clients", json={"name": "B"}).json()
        client.patch(f"/api/v1/clients/{a['id']}", json={"archived": True})
        r = client.get("/api/v1/clients?include_archived=true")
        assert len(r.json()) == 2

    def test_patch_updates_name(self, client: TestClient):
        created = client.post("/api/v1/clients", json={"name": "EMSA"}).json()
        r = client.patch(f"/api/v1/clients/{created['id']}", json={"name": "EMSA-2"})
        assert r.status_code == 200
        assert r.json()["name"] == "EMSA-2"

    def test_patch_missing_returns_404(self, client: TestClient):
        r = client.patch(f"/api/v1/clients/{uuid4()}", json={"name": "X"})
        assert r.status_code == 404

    def test_delete_returns_204(self, client: TestClient):
        created = client.post("/api/v1/clients", json={"name": "EMSA"}).json()
        r = client.delete(f"/api/v1/clients/{created['id']}")
        assert r.status_code == 204
        assert client.get(f"/api/v1/clients/{created['id']}").status_code == 404

    def test_delete_missing_returns_404(self, client: TestClient):
        r = client.delete(f"/api/v1/clients/{uuid4()}")
        assert r.status_code == 404
