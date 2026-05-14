# SPDX-License-Identifier: GPL-3.0-or-later
import sqlite3
from contextlib import closing
from pathlib import Path

from colourlog.adapters.persistence.sqlite.engine import connect
from fastapi.testclient import TestClient


class TestFullWorkflowThroughSqlite:
    """End-to-end-ish: HTTP → use cases → SQLite. Verifies the wiring is sound."""

    def test_create_hierarchy_and_track_entry(self, client: TestClient, db_path: Path):
        # 1. create client
        c = client.post("/api/v1/clients", json={"name": "EMSA"}).json()
        # 2. create project under client
        p = client.post("/api/v1/projects", json={"name": "Evvue", "client_id": c["id"]}).json()
        # 3. create task under project
        t = client.post("/api/v1/tasks", json={"name": "T41622", "project_id": p["id"]}).json()
        # 4. start entry
        start = client.post("/api/v1/entries/start", json={"task_id": t["id"]})
        assert start.status_code == 201
        # 5. current task reflects running entry
        current = client.get("/api/v1/tasks/current").json()
        assert current is not None
        assert current["task"]["id"] == t["id"]
        # 6. stop entry
        stop = client.post("/api/v1/entries/stop")
        assert stop.status_code == 201
        assert stop.json()["task_id"] is None
        # 7. no current task after stop
        assert client.get("/api/v1/tasks/current").json() is None
        # 8. entries list projects exactly one entry (the start), end populated
        entries = client.get("/api/v1/entries").json()
        assert len(entries) == 1
        assert entries[0]["task_id"] == t["id"]
        assert entries[0]["end"] is not None

    def test_sqlite_state_matches_api(self, client: TestClient, db_path: Path):
        c = client.post("/api/v1/clients", json={"name": "EMSA"}).json()
        p = client.post("/api/v1/projects", json={"name": "Evvue", "client_id": c["id"]}).json()
        client.post(
            "/api/v1/tasks",
            json={"name": "T41622", "project_id": p["id"], "keywords": ["foo"]},
        )
        with closing(connect(db_path)) as conn:
            conn.row_factory = sqlite3.Row
            tasks_rows = conn.execute("SELECT name, keywords FROM tasks").fetchall()
            projects_rows = conn.execute("SELECT name, client_id FROM projects").fetchall()
            clients_rows = conn.execute("SELECT name FROM clients").fetchall()
        assert clients_rows[0]["name"] == "EMSA"
        assert projects_rows[0]["client_id"] == c["id"]
        assert tasks_rows[0]["name"] == "T41622"
        assert tasks_rows[0]["keywords"] == '["foo"]'

    def test_entry_events_table_records_appends(self, client: TestClient, db_path: Path):
        p = client.post("/api/v1/projects", json={"name": "P"}).json()
        t = client.post("/api/v1/tasks", json={"name": "T", "project_id": p["id"]}).json()
        client.post("/api/v1/entries/start", json={"task_id": t["id"]})
        client.post("/api/v1/entries/stop")
        client.post("/api/v1/entries/start", json={"task_id": t["id"]})
        with closing(connect(db_path)) as conn:
            rows = conn.execute("SELECT task_id, source FROM entry_events ORDER BY ts").fetchall()
        assert len(rows) == 3
        # start, stop, start
        assert rows[0][0] == t["id"]
        assert rows[0][1] == "manual"
        assert rows[1][0] is None
        assert rows[1][1] is None
        assert rows[2][0] == t["id"]

    def test_404_envelope_through_full_stack(self, client: TestClient):
        r = client.get("/api/v1/clients/00000000-0000-0000-0000-000000000000")
        assert r.status_code == 404
        assert r.json()["error"]["code"] == "client_not_found"

    def test_invalid_name_envelope_through_full_stack(self, client: TestClient):
        r = client.post("/api/v1/clients", json={"name": "   "})
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "invalid_name"
