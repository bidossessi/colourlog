# SPDX-License-Identifier: GPL-3.0-or-later
import sqlite3
from contextlib import closing
from pathlib import Path
from uuid import UUID

from colourlog.adapters.persistence.sqlite.engine import connect
from colourlog.domain.entities import Project


def _row_to_project(row: sqlite3.Row) -> Project:
    client_id_raw = row["client_id"]
    return Project(
        id=UUID(row["id"]),
        name=row["name"],
        client_id=UUID(client_id_raw) if client_id_raw is not None else None,
        archived=bool(row["archived"]),
    )


class SqliteProjectRepository:
    def __init__(self, database_path: Path | str) -> None:
        self._path = database_path

    def add(self, project: Project) -> None:
        with closing(connect(self._path)) as conn, conn:
            conn.execute(
                "INSERT INTO projects (id, name, client_id, archived) VALUES (?, ?, ?, ?)",
                (
                    str(project.id),
                    project.name,
                    str(project.client_id) if project.client_id is not None else None,
                    int(project.archived),
                ),
            )

    def get(self, id: UUID) -> Project | None:
        with closing(connect(self._path)) as conn:
            row = conn.execute(
                "SELECT id, name, client_id, archived FROM projects WHERE id = ?",
                (str(id),),
            ).fetchone()
        return _row_to_project(row) if row is not None else None

    def list(
        self,
        *,
        client_id: UUID | None = None,
        include_archived: bool = False,
    ) -> list[Project]:
        sql = "SELECT id, name, client_id, archived FROM projects"
        params: list[object] = []
        conditions: list[str] = []
        if client_id is not None:
            conditions.append("client_id = ?")
            params.append(str(client_id))
        if not include_archived:
            conditions.append("archived = 0")
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY name"
        with closing(connect(self._path)) as conn:
            rows = conn.execute(sql, params).fetchall()
        return [_row_to_project(r) for r in rows]

    def update(self, project: Project) -> None:
        with closing(connect(self._path)) as conn, conn:
            conn.execute(
                "UPDATE projects SET name = ?, client_id = ?, archived = ? WHERE id = ?",
                (
                    project.name,
                    str(project.client_id) if project.client_id is not None else None,
                    int(project.archived),
                    str(project.id),
                ),
            )

    def delete(self, id: UUID) -> None:
        with closing(connect(self._path)) as conn, conn:
            conn.execute("DELETE FROM projects WHERE id = ?", (str(id),))
