# SPDX-License-Identifier: GPL-3.0-or-later
import sqlite3
from contextlib import closing
from pathlib import Path
from uuid import UUID

from colourlog.adapters.persistence.sqlite.engine import connect
from colourlog.domain.entities import Client


def _row_to_client(row: sqlite3.Row) -> Client:
    return Client(
        id=UUID(row["id"]),
        name=row["name"],
        archived=bool(row["archived"]),
    )


class SqliteClientRepository:
    def __init__(self, database_path: Path | str) -> None:
        self._path = database_path

    def add(self, client: Client) -> None:
        with closing(connect(self._path)) as conn, conn:
            conn.execute(
                "INSERT INTO clients (id, name, archived) VALUES (?, ?, ?)",
                (str(client.id), client.name, int(client.archived)),
            )

    def get(self, id: UUID) -> Client | None:
        with closing(connect(self._path)) as conn:
            row = conn.execute(
                "SELECT id, name, archived FROM clients WHERE id = ?",
                (str(id),),
            ).fetchone()
        return _row_to_client(row) if row is not None else None

    def list(self, *, include_archived: bool = False) -> list[Client]:
        sql = "SELECT id, name, archived FROM clients"
        if not include_archived:
            sql += " WHERE archived = 0"
        sql += " ORDER BY name"
        with closing(connect(self._path)) as conn:
            rows = conn.execute(sql).fetchall()
        return [_row_to_client(r) for r in rows]

    def update(self, client: Client) -> None:
        with closing(connect(self._path)) as conn, conn:
            conn.execute(
                "UPDATE clients SET name = ?, archived = ? WHERE id = ?",
                (client.name, int(client.archived), str(client.id)),
            )

    def delete(self, id: UUID) -> None:
        with closing(connect(self._path)) as conn, conn:
            conn.execute("DELETE FROM clients WHERE id = ?", (str(id),))
