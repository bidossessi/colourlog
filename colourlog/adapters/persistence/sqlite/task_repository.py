# SPDX-License-Identifier: GPL-3.0-or-later
import json
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path
from uuid import UUID

from colourlog.adapters.persistence.sqlite.engine import connect
from colourlog.domain.entities import Task


def _row_to_task(row: sqlite3.Row) -> Task:
    return Task(
        id=UUID(row["id"]),
        name=row["name"],
        project_id=UUID(row["project_id"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        code=row["code"],
        tags=tuple(json.loads(row["tags"])),
        keywords=tuple(json.loads(row["keywords"])),
        archived=bool(row["archived"]),
    )


class SqliteTaskRepository:
    def __init__(self, database_path: Path | str) -> None:
        self._path = database_path

    def add(self, task: Task) -> None:
        with closing(connect(self._path)) as conn, conn:
            conn.execute(
                "INSERT INTO tasks "
                "(id, name, project_id, code, tags, keywords, created_at, archived) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    str(task.id),
                    task.name,
                    str(task.project_id),
                    task.code,
                    json.dumps(list(task.tags)),
                    json.dumps(list(task.keywords)),
                    task.created_at.isoformat(),
                    int(task.archived),
                ),
            )

    def get(self, id: UUID) -> Task | None:
        with closing(connect(self._path)) as conn:
            row = conn.execute(
                "SELECT id, name, project_id, code, tags, keywords, created_at, "
                "archived FROM tasks WHERE id = ?",
                (str(id),),
            ).fetchone()
        return _row_to_task(row) if row is not None else None

    def list(
        self,
        *,
        project_id: UUID | None = None,
        include_archived: bool = False,
    ) -> list[Task]:
        sql = "SELECT id, name, project_id, code, tags, keywords, created_at, archived FROM tasks"
        params: list[object] = []
        conditions: list[str] = []
        if project_id is not None:
            conditions.append("project_id = ?")
            params.append(str(project_id))
        if not include_archived:
            conditions.append("archived = 0")
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY created_at"
        with closing(connect(self._path)) as conn:
            rows = conn.execute(sql, params).fetchall()
        return [_row_to_task(r) for r in rows]

    def update(self, task: Task) -> None:
        with closing(connect(self._path)) as conn, conn:
            conn.execute(
                "UPDATE tasks SET name = ?, project_id = ?, code = ?, "
                "tags = ?, keywords = ?, archived = ? WHERE id = ?",
                (
                    task.name,
                    str(task.project_id),
                    task.code,
                    json.dumps(list(task.tags)),
                    json.dumps(list(task.keywords)),
                    int(task.archived),
                    str(task.id),
                ),
            )

    def delete(self, id: UUID) -> None:
        with closing(connect(self._path)) as conn, conn:
            conn.execute("DELETE FROM tasks WHERE id = ?", (str(id),))
