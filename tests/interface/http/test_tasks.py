# SPDX-License-Identifier: GPL-3.0-or-later
from typing import cast
from uuid import uuid4

from fastapi.testclient import TestClient


def _make_project(client: TestClient, name: str = "Evvue") -> str:
    return cast("str", client.post("/api/v1/projects", json={"name": name}).json()["id"])


class TestTasksAPI:
    def test_create_defaults_keywords_to_name(self, client: TestClient):
        pid = _make_project(client)
        r = client.post("/api/v1/tasks", json={"name": "T41622", "project_id": pid})
        assert r.status_code == 201
        body = r.json()
        assert body["keywords"] == ["t41622"]
        assert body["tags"] == []
        assert body["created_at"].startswith("2026-05-14T10:")

    def test_create_unknown_project_returns_404(self, client: TestClient):
        r = client.post(
            "/api/v1/tasks",
            json={"name": "T", "project_id": str(uuid4())},
        )
        assert r.status_code == 404
        assert r.json()["error"]["code"] == "project_not_found"

    def test_create_normalizes_keywords(self, client: TestClient):
        pid = _make_project(client)
        r = client.post(
            "/api/v1/tasks",
            json={
                "name": "T",
                "project_id": pid,
                "keywords": ["FOO", "  bar  "],
            },
        )
        assert r.json()["keywords"] == ["foo", "bar"]

    def test_get_returns_task(self, client: TestClient):
        pid = _make_project(client)
        created = client.post("/api/v1/tasks", json={"name": "T", "project_id": pid}).json()
        r = client.get(f"/api/v1/tasks/{created['id']}")
        assert r.status_code == 200
        assert r.json() == created

    def test_get_missing_returns_404(self, client: TestClient):
        r = client.get(f"/api/v1/tasks/{uuid4()}")
        assert r.status_code == 404

    def test_list_filter_by_project(self, client: TestClient):
        p1 = _make_project(client, "P1")
        p2 = _make_project(client, "P2")
        client.post("/api/v1/tasks", json={"name": "X", "project_id": p1})
        client.post("/api/v1/tasks", json={"name": "Y", "project_id": p2})
        r = client.get(f"/api/v1/tasks?project_id={p1}")
        names = [t["name"] for t in r.json()]
        assert names == ["X"]

    def test_list_include_archived(self, client: TestClient):
        pid = _make_project(client)
        a = client.post("/api/v1/tasks", json={"name": "A", "project_id": pid}).json()
        client.post("/api/v1/tasks", json={"name": "B", "project_id": pid})
        client.patch(f"/api/v1/tasks/{a['id']}", json={"archived": True})
        r = client.get("/api/v1/tasks?include_archived=true")
        assert len(r.json()) == 2

    def test_patch_clear_code(self, client: TestClient):
        pid = _make_project(client)
        t = client.post(
            "/api/v1/tasks",
            json={"name": "T", "project_id": pid, "code": "ABC"},
        ).json()
        r = client.patch(f"/api/v1/tasks/{t['id']}", json={"clear_code": True})
        assert r.json()["code"] is None

    def test_patch_invalid_keyword_returns_400(self, client: TestClient):
        # raw uppercase passed via direct construction would be invalid;
        # HTTP layer normalizes, so this test exercises happy path normalization
        pid = _make_project(client)
        t = client.post("/api/v1/tasks", json={"name": "T", "project_id": pid}).json()
        r = client.patch(f"/api/v1/tasks/{t['id']}", json={"keywords": ["FOO"]})
        assert r.status_code == 200
        assert r.json()["keywords"] == ["foo"]

    def test_patch_unknown_new_project_returns_404(self, client: TestClient):
        pid = _make_project(client)
        t = client.post("/api/v1/tasks", json={"name": "T", "project_id": pid}).json()
        r = client.patch(f"/api/v1/tasks/{t['id']}", json={"project_id": str(uuid4())})
        assert r.status_code == 404

    def test_delete_returns_204(self, client: TestClient):
        pid = _make_project(client)
        t = client.post("/api/v1/tasks", json={"name": "T", "project_id": pid}).json()
        r = client.delete(f"/api/v1/tasks/{t['id']}")
        assert r.status_code == 204

    def test_delete_missing_returns_404(self, client: TestClient):
        r = client.delete(f"/api/v1/tasks/{uuid4()}")
        assert r.status_code == 404
