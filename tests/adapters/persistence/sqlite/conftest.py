# SPDX-License-Identifier: GPL-3.0-or-later
from contextlib import closing
from pathlib import Path

import pytest
from colourlog.adapters.persistence.sqlite.engine import connect, init_schema


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "test.sqlite"
    with closing(connect(path)) as conn:
        init_schema(conn)
    return path
