# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path

from colourlog.adapters.persistence.sqlite.mode_repository import (
    SqliteModeRepository,
)
from colourlog.domain.value_objects import Mode


class TestSqliteModeRepository:
    def test_defaults_to_manual_when_row_absent(self, db_path: Path):
        assert SqliteModeRepository(db_path).get() is Mode.MANUAL

    def test_set_then_get(self, db_path: Path):
        repo = SqliteModeRepository(db_path)
        repo.set(Mode.AUTO)
        assert repo.get() is Mode.AUTO

    def test_set_upserts(self, db_path: Path):
        repo = SqliteModeRepository(db_path)
        repo.set(Mode.AUTO)
        repo.set(Mode.MANUAL)
        assert repo.get() is Mode.MANUAL
