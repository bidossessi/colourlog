# SPDX-License-Identifier: GPL-3.0-or-later
from datetime import UTC, datetime
from uuid import uuid4

import httpx
import pytest
from colourlog.interface.tray.client import (
    CurrentTaskView,
    DaemonUnreachableError,
    TaskSummary,
    TrayClient,
)


def _client_with_handler(handler: object) -> TrayClient:
    transport = httpx.MockTransport(handler)  # type: ignore[arg-type]
    client = TrayClient(base_url="http://daemon")
    client._client = httpx.Client(transport=transport, base_url="http://daemon")
    return client


class TestListTasks:
    def test_returns_tasks(self):
        task_id = uuid4()

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/api/v1/tasks"
            return httpx.Response(
                200,
                json=[
                    {"id": str(task_id), "name": "T41622", "archived": False},
                ],
            )

        with _client_with_handler(handler) as client:
            tasks = client.list_tasks()
        assert tasks == [TaskSummary(id=task_id, name="T41622", archived=False)]

    def test_daemon_unreachable_raises(self):
        def handler(_request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("refused")

        with _client_with_handler(handler) as client, pytest.raises(DaemonUnreachableError):
            client.list_tasks()


class TestCurrentTask:
    def test_returns_view_when_running(self):
        task_id = uuid4()
        started = datetime(2026, 5, 14, 10, 0, tzinfo=UTC)

        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "task": {"id": str(task_id), "name": "T41622"},
                    "entry": {
                        "source": "manual",
                        "start": started.isoformat(),
                    },
                },
            )

        with _client_with_handler(handler) as client:
            view = client.current_task()
        assert view == CurrentTaskView(
            task_id=task_id,
            task_name="T41622",
            source="manual",
            started_at=started,
        )

    def test_returns_none_when_idle(self):
        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                content=b"null",
                headers={"content-type": "application/json"},
            )

        with _client_with_handler(handler) as client:
            assert client.current_task() is None

    def test_daemon_unreachable_raises(self):
        def handler(_request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("refused")

        with _client_with_handler(handler) as client, pytest.raises(DaemonUnreachableError):
            client.current_task()


class TestStartEntry:
    def test_posts_minimum_body(self):
        task_id = uuid4()
        captured: dict[str, object] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["url"] = str(request.url)
            captured["body"] = request.content.decode()
            return httpx.Response(
                201,
                json={
                    "id": str(uuid4()),
                    "task_id": str(task_id),
                    "ts": "2026-05-14T10:00:00+00:00",
                    "source": "manual",
                    "subtask_id": None,
                    "match_source": None,
                    "matched_keyword": None,
                    "calendar_event_id": None,
                    "note": None,
                },
            )

        with _client_with_handler(handler) as client:
            client.start_entry(task_id=task_id)
        assert "/api/v1/entries/start" in str(captured["url"])
        body_text = cast_str(captured["body"])
        assert str(task_id) in body_text

    def test_includes_optional_fields(self):
        task_id = uuid4()
        subtask_id = uuid4()
        captured: dict[str, str] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["body"] = request.content.decode()
            return httpx.Response(
                201,
                json={
                    "id": str(uuid4()),
                    "task_id": str(task_id),
                    "ts": "2026-05-14T10:00:00+00:00",
                    "source": "manual",
                    "subtask_id": str(subtask_id),
                    "match_source": None,
                    "matched_keyword": None,
                    "calendar_event_id": None,
                    "note": "focus",
                },
            )

        with _client_with_handler(handler) as client:
            client.start_entry(task_id=task_id, subtask_id=subtask_id, note="focus")
        assert str(subtask_id) in captured["body"]
        assert "focus" in captured["body"]

    def test_daemon_unreachable_raises(self):
        def handler(_request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("refused")

        with _client_with_handler(handler) as client, pytest.raises(DaemonUnreachableError):
            client.start_entry(task_id=uuid4())


class TestStopEntry:
    def test_posts_stop(self):
        captured: dict[str, str] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["url"] = str(request.url)
            return httpx.Response(
                201,
                json={
                    "id": str(uuid4()),
                    "task_id": None,
                    "ts": "2026-05-14T10:00:00+00:00",
                    "source": None,
                    "subtask_id": None,
                    "match_source": None,
                    "matched_keyword": None,
                    "calendar_event_id": None,
                    "note": None,
                },
            )

        with _client_with_handler(handler) as client:
            client.stop_entry()
        assert "/api/v1/entries/stop" in captured["url"]

    def test_daemon_unreachable_raises(self):
        def handler(_request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("refused")

        with _client_with_handler(handler) as client, pytest.raises(DaemonUnreachableError):
            client.stop_entry()


def cast_str(value: object) -> str:
    assert isinstance(value, str)
    return value
