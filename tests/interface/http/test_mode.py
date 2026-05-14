# SPDX-License-Identifier: GPL-3.0-or-later
from fastapi.testclient import TestClient


class TestModeAPI:
    def test_get_defaults_to_manual(self, client: TestClient):
        r = client.get("/api/v1/mode")
        assert r.status_code == 200
        assert r.json() == {"mode": "manual"}

    def test_patch_to_auto(self, client: TestClient):
        r = client.patch("/api/v1/mode", json={"mode": "auto"})
        assert r.status_code == 200
        assert r.json() == {"mode": "auto"}
        # subsequent GET reflects change
        assert client.get("/api/v1/mode").json() == {"mode": "auto"}

    def test_patch_invalid_returns_422(self, client: TestClient):
        r = client.patch("/api/v1/mode", json={"mode": "nope"})
        assert r.status_code == 422
