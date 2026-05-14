# SPDX-License-Identifier: GPL-3.0-or-later
# mypy: ignore-errors
# ruff: noqa: I001
"""GTK3 + AyatanaAppIndicator3 tray. Ubuntu 24.04 path (PyGObject<3.50).

GUI module — not type-checked or coverage-tracked. Tested manually via
acceptance run (`make tray` against a running daemon).
"""

import logging
import threading
from collections.abc import Callable

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("AyatanaAppIndicator3", "0.1")
from gi.repository import AyatanaAppIndicator3, GLib, Gtk  # noqa: E402

import httpx  # noqa: E402

from colourlog.interface.tray.client import (  # noqa: E402
    DaemonUnreachableError,
    TaskSummary,
    TrayClient,
)
from colourlog.interface.tray.state import TrayView, render  # noqa: E402

logger = logging.getLogger(__name__)


class TaskPickerDialog(Gtk.Dialog):
    """Modal task picker with substring filter; double-click or OK to confirm."""

    def __init__(self, parent: Gtk.Window | None, tasks: list[TaskSummary]) -> None:
        super().__init__(title="Start a task", transient_for=parent, modal=True)
        self.set_default_size(360, 420)
        self.add_buttons(
            "Cancel",
            Gtk.ResponseType.CANCEL,
            "Start",
            Gtk.ResponseType.OK,
        )
        self._tasks = tasks
        self._selected: TaskSummary | None = None

        box = self.get_content_area()
        box.set_spacing(6)
        box.set_margin_top(8)
        box.set_margin_bottom(8)
        box.set_margin_start(8)
        box.set_margin_end(8)

        self._filter_entry = Gtk.Entry()
        self._filter_entry.set_placeholder_text("Filter…")
        self._filter_entry.connect("changed", self._on_filter_changed)
        box.add(self._filter_entry)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        box.add(scrolled)

        self._listbox = Gtk.ListBox()
        self._listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self._listbox.connect("row-activated", self._on_row_activated)
        scrolled.add(self._listbox)

        self._populate(tasks)
        self.show_all()

    def _populate(self, tasks: list[TaskSummary]) -> None:
        for child in self._listbox.get_children():
            self._listbox.remove(child)
        for task in tasks:
            row = Gtk.ListBoxRow()
            row.task = task
            label = Gtk.Label(label=task.name, xalign=0.0)
            label.set_margin_top(4)
            label.set_margin_bottom(4)
            label.set_margin_start(8)
            row.add(label)
            self._listbox.add(row)
        self._listbox.show_all()
        if tasks:
            self._listbox.select_row(self._listbox.get_row_at_index(0))

    def _on_filter_changed(self, entry: Gtk.Entry) -> None:
        needle = entry.get_text().strip().lower()
        if not needle:
            self._populate(self._tasks)
            return
        filtered = [t for t in self._tasks if needle in t.name.lower()]
        self._populate(filtered)

    def _on_row_activated(self, _listbox: Gtk.ListBox, row: Gtk.ListBoxRow) -> None:
        self._selected = row.task
        self.response(Gtk.ResponseType.OK)

    def chosen(self) -> TaskSummary | None:
        if self._selected is not None:
            return self._selected
        row = self._listbox.get_selected_row()
        if row is None:
            return None
        return row.task


class TrayApp:
    def __init__(self, daemon_url: str) -> None:
        self._daemon_url = daemon_url.rstrip("/")
        self._client = TrayClient(base_url=self._daemon_url)
        self._stop_evt = threading.Event()
        self._sse_thread: threading.Thread | None = None

        self._indicator = AyatanaAppIndicator3.Indicator.new(
            "colourlog-tray",
            "media-playback-stop",
            AyatanaAppIndicator3.IndicatorCategory.APPLICATION_STATUS,
        )
        self._indicator.set_status(AyatanaAppIndicator3.IndicatorStatus.ACTIVE)

        self._menu = Gtk.Menu()
        self._mi_label = self._add_item("—: idle", None, sensitive=False)
        self._menu.append(Gtk.SeparatorMenuItem())
        self._mi_start = self._add_item("Start a Task…", self._on_start)
        self._mi_stop = self._add_item("Stop tracking", self._on_stop)
        self._menu.append(Gtk.SeparatorMenuItem())
        self._add_item("Exit", self._on_exit)
        self._menu.show_all()
        self._indicator.set_menu(self._menu)

    def _add_item(
        self,
        label: str,
        callback: Callable[[Gtk.MenuItem], None] | None,
        sensitive: bool = True,
    ) -> Gtk.MenuItem:
        item = Gtk.MenuItem(label=label)
        item.set_sensitive(sensitive)
        if callback is not None:
            item.connect("activate", callback)
        self._menu.append(item)
        return item

    # ---- UI update path (called on GTK thread via GLib.idle_add) ----

    def _apply_view(self, view: TrayView) -> bool:
        self._indicator.set_icon_full(view.icon_name, view.label)
        self._indicator.set_label(view.label, "")
        self._mi_label.set_label(view.label)
        # enable Stop only when running
        self._mi_stop.set_sensitive(view.icon.value == "running")
        return False  # GLib.idle_add: don't re-schedule

    # ---- background refresh path ----

    def _refresh(self) -> None:
        try:
            current = self._client.current_task()
            online = True
        except DaemonUnreachableError:
            current = None
            online = False
        except httpx.HTTPError as exc:
            logger.warning("daemon HTTP error during refresh: %s", exc)
            current = None
            online = False
        view = render(current, daemon_online=online)
        GLib.idle_add(self._apply_view, view)

    # ---- menu callbacks ----

    def _on_start(self, _item: Gtk.MenuItem) -> None:
        try:
            tasks = self._client.list_tasks()
        except DaemonUnreachableError:
            logger.warning("daemon unreachable, cannot list tasks")
            return
        dialog = TaskPickerDialog(parent=None, tasks=tasks)
        response = dialog.run()
        chosen = dialog.chosen() if response == Gtk.ResponseType.OK else None
        dialog.destroy()
        if chosen is None:
            return
        try:
            self._client.start_entry(task_id=chosen.id)
        except DaemonUnreachableError:
            logger.warning("daemon unreachable, start_entry failed")
        # SSE will push the update; immediate refresh as fallback
        threading.Thread(target=self._refresh, daemon=True).start()

    def _on_stop(self, _item: Gtk.MenuItem) -> None:
        try:
            self._client.stop_entry()
        except DaemonUnreachableError:
            logger.warning("daemon unreachable, stop_entry failed")
        threading.Thread(target=self._refresh, daemon=True).start()

    def _on_exit(self, _item: Gtk.MenuItem) -> None:
        self._stop_evt.set()
        self._client.close()
        Gtk.main_quit()

    # ---- SSE consumer ----

    def _sse_loop(self) -> None:
        backoff = 1.0
        sse_timeout = httpx.Timeout(connect=10.0, read=None, write=10.0, pool=10.0)
        while not self._stop_evt.is_set():
            try:
                with (
                    httpx.Client(base_url=self._daemon_url, timeout=sse_timeout) as c,
                    c.stream("GET", "/api/v1/events") as response,
                ):
                    response.raise_for_status()
                    backoff = 1.0
                    GLib.idle_add(self._apply_view, render(None, daemon_online=True))
                    threading.Thread(target=self._refresh, daemon=True).start()
                    for line in response.iter_lines():
                        if self._stop_evt.is_set():
                            return
                        if line.startswith("event: ") or line.startswith("data: "):
                            threading.Thread(target=self._refresh, daemon=True).start()
            except (httpx.HTTPError, httpx.RequestError) as exc:
                logger.info("SSE disconnected: %s; retrying in %.0fs", exc, backoff)
                GLib.idle_add(self._apply_view, render(None, daemon_online=False))
                self._stop_evt.wait(backoff)
                backoff = min(backoff * 2, 30.0)

    # ---- run loop ----

    def run(self) -> None:
        self._sse_thread = threading.Thread(target=self._sse_loop, daemon=True)
        self._sse_thread.start()
        threading.Thread(target=self._refresh, daemon=True).start()
        Gtk.main()


def main() -> None:
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    parser = argparse.ArgumentParser(prog="colourlog-tray")
    parser.add_argument(
        "--daemon-url",
        default="http://127.0.0.1:18765",
        help="base URL of the colourlog daemon",
    )
    args = parser.parse_args()
    TrayApp(daemon_url=args.daemon_url).run()
