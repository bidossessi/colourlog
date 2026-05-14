# SPDX-License-Identifier: GPL-3.0-or-later
from fastapi.testclient import TestClient


def test_healthz_returns_ok(client: TestClient):
    r = client.get("/healthz")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["version"]
