# SPDX-License-Identifier: GPL-3.0-or-later
from contextlib import closing
from pathlib import Path
from typing import Final

from colourlog.adapters.persistence.sqlite.engine import connect
from colourlog.domain.value_objects import Mode

_KEY: Final = "mode"
_SELECT_SQL: Final = "SELECT value FROM daemon_state WHERE key = ?"
_UPSERT_SQL: Final = (
    "INSERT INTO daemon_state (key, value) VALUES (?, ?) "
    "ON CONFLICT(key) DO UPDATE SET value = excluded.value"
)


class SqliteModeRepository:
    def __init__(self, database_path: Path | str) -> None:
        self._path = database_path

    def get(self) -> Mode:
        with closing(connect(self._path)) as conn:
            row = conn.execute(_SELECT_SQL, (_KEY,)).fetchone()
        return Mode(row["value"]) if row is not None else Mode.MANUAL

    def set(self, mode: Mode) -> None:
        with closing(connect(self._path)) as conn, conn:
            conn.execute(_UPSERT_SQL, (_KEY, mode.value))
