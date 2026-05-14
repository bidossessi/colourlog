# SPDX-License-Identifier: GPL-3.0-or-later
from typing import cast
from uuid import uuid4

from fastapi.testclient import TestClient


def _make_project(client: TestClient, name: str = "Evvue") -> str:
    return cast(
        "str",
        client.post("/api/v1/projects", json={"name": name}).json()["id"],
    )


def _make_task(client: TestClient, project_id: str, name: str = "T41622") -> str:
    return cast(
        "str",
        client.post("/api/v1/tasks", json={"name": name, "project_id": project_id}).json()["id"],
    )


class TestEntriesStart:
    def test_start_appends_event(self, client: TestClient):
        pid = _make_project(client)
        tid = _make_task(client, pid)
        r = client.post("/api/v1/entries/start", json={"task_id": tid})
        assert r.status_code == 201
        body = r.json()
        assert body["task_id"] == tid
        assert body["source"] == "manual"
        assert body["subtask_id"] is None

    def test_start_with_subtask(self, client: TestClient):
        pid = _make_project(client)
        tid = _make_task(client, pid, "T41622")
        sub = _make_task(client, pid, "D12345")
        r = client.post("/api/v1/entries/start", json={"task_id": tid, "subtask_id": sub})
        assert r.status_code == 201
        assert r.json()["subtask_id"] == sub

    def test_start_with_note_normalized(self, client: TestClient):
        pid = _make_project(client)
        tid = _make_task(client, pid)
        r = client.post("/api/v1/entries/start", json={"task_id": tid, "note": "  focus  "})
        assert r.json()["note"] == "focus"

    def test_start_unknown_task_returns_404(self, client: TestClient):
        r = client.post("/api/v1/entries/start", json={"task_id": str(uuid4())})
        assert r.status_code == 404
        assert r.json()["error"]["code"] == "task_not_found"

    def test_start_unknown_subtask_returns_404(self, client: TestClient):
        pid = _make_project(client)
        tid = _make_task(client, pid)
        r = client.post(
            "/api/v1/entries/start",
            json={"task_id": tid, "subtask_id": str(uuid4())},
        )
        assert r.status_code == 404


class TestEntriesStop:
    def test_stop_appends_event(self, client: TestClient):
        pid = _make_project(client)
        tid = _make_task(client, pid)
        client.post("/api/v1/entries/start", json={"task_id": tid})
        r = client.post("/api/v1/entries/stop")
        assert r.status_code == 201
        body = r.json()
        assert body["task_id"] is None
        assert body["source"] is None

    def test_stop_with_nothing_running_still_appends(self, client: TestClient):
        r = client.post("/api/v1/entries/stop")
        assert r.status_code == 201
        assert r.json()["task_id"] is None


class TestEntriesList:
    def test_pairs_consecutive_into_entries(self, client: TestClient):
        pid = _make_project(client)
        tid = _make_task(client, pid)
        client.post("/api/v1/entries/start", json={"task_id": tid})
        # frozen clock: all events at same ts → fine for shape, just one entry.
        items = client.get("/api/v1/entries").json()
        assert len(items) == 1
        assert items[0]["task_id"] == tid

    def test_filter_by_task(self, client: TestClient):
        pid = _make_project(client)
        t1 = _make_task(client, pid, "A")
        t2 = _make_task(client, pid, "B")
        client.post("/api/v1/entries/start", json={"task_id": t1})
        client.post("/api/v1/entries/start", json={"task_id": t2})
        r = client.get(f"/api/v1/entries?task_id={t1}")
        items = r.json()
        assert len(items) == 1
        assert items[0]["task_id"] == t1


class TestCurrentTaskAPI:
    def test_null_when_no_event(self, client: TestClient):
        r = client.get("/api/v1/tasks/current")
        assert r.status_code == 200
        assert r.json() is None

    def test_returns_entry_and_task(self, client: TestClient):
        pid = _make_project(client)
        tid = _make_task(client, pid)
        client.post("/api/v1/entries/start", json={"task_id": tid})
        r = client.get("/api/v1/tasks/current")
        body = r.json()
        assert body is not None
        assert body["task"]["id"] == tid
        assert body["entry"]["task_id"] == tid
        assert body["entry"]["end"] is None

    def test_null_after_stop(self, client: TestClient):
        pid = _make_project(client)
        tid = _make_task(client, pid)
        client.post("/api/v1/entries/start", json={"task_id": tid})
        client.post("/api/v1/entries/stop")
        r = client.get("/api/v1/tasks/current")
        assert r.json() is None
