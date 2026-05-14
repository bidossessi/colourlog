# SPDX-License-Identifier: GPL-3.0-or-later
from datetime import UTC, datetime

import httpx
from colourlog.adapters.activitywatch.http_client import AwHttpReader


def _reader_with_handler(handler: object, hostname: str = "host") -> AwHttpReader:
    reader = AwHttpReader(hostname=hostname)
    reader._client = httpx.Client(
        transport=httpx.MockTransport(handler),  # type: ignore[arg-type]
        base_url="http://aw",
    )
    return reader


class TestLatestWindow:
    def test_parses_window_event(self):
        ts = "2026-05-14T20:00:00+00:00"

        def handler(request: httpx.Request) -> httpx.Response:
            assert "aw-watcher-window_host" in str(request.url)
            return httpx.Response(
                200,
                json=[
                    {
                        "id": 1,
                        "timestamp": ts,
                        "duration": 5.0,
                        "data": {"app": "Code", "title": "main.py"},
                    }
                ],
            )

        with _reader_with_handler(handler) as r:
            window = r.latest_window()
        assert window is not None
        assert window.app == "Code"
        assert window.title == "main.py"
        assert window.url is None
        assert window.ts == datetime(2026, 5, 14, 20, 0, tzinfo=UTC)

    def test_url_when_present(self):
        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json=[
                    {
                        "id": 1,
                        "timestamp": "2026-05-14T20:00:00+00:00",
                        "duration": 0.0,
                        "data": {
                            "app": "Chrome",
                            "title": "Docs",
                            "url": "https://x.test",
                        },
                    }
                ],
            )

        with _reader_with_handler(handler) as r:
            window = r.latest_window()
        assert window is not None
        assert window.url == "https://x.test"

    def test_empty_bucket_returns_none(self):
        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=[])

        with _reader_with_handler(handler) as r:
            assert r.latest_window() is None

    def test_non_200_returns_none(self):
        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, json={"error": "no bucket"})

        with _reader_with_handler(handler) as r:
            assert r.latest_window() is None

    def test_connect_error_returns_none(self):
        def handler(_request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("refused")

        with _reader_with_handler(handler) as r:
            assert r.latest_window() is None


class TestLatestAfk:
    def test_parses_not_afk(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert "aw-watcher-afk_host" in str(request.url)
            return httpx.Response(
                200,
                json=[
                    {
                        "id": 1,
                        "timestamp": "2026-05-14T20:00:00+00:00",
                        "duration": 42.5,
                        "data": {"status": "not-afk"},
                    }
                ],
            )

        with _reader_with_handler(handler) as r:
            afk = r.latest_afk()
        assert afk is not None
        assert afk.status == "not-afk"
        assert afk.duration_seconds == 42.5

    def test_parses_afk(self):
        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json=[
                    {
                        "id": 1,
                        "timestamp": "2026-05-14T20:00:00+00:00",
                        "duration": 300.0,
                        "data": {"status": "afk"},
                    }
                ],
            )

        with _reader_with_handler(handler) as r:
            afk = r.latest_afk()
        assert afk is not None
        assert afk.status == "afk"

    def test_unknown_status_returns_none(self):
        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json=[
                    {
                        "id": 1,
                        "timestamp": "2026-05-14T20:00:00+00:00",
                        "duration": 0.0,
                        "data": {"status": "weird"},
                    }
                ],
            )

        with _reader_with_handler(handler) as r:
            assert r.latest_afk() is None

    def test_empty_returns_none(self):
        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=[])

        with _reader_with_handler(handler) as r:
            assert r.latest_afk() is None
