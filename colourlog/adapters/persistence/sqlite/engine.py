# SPDX-License-Identifier: GPL-3.0-or-later
import sqlite3
from pathlib import Path

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS clients (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    archived INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    client_id TEXT REFERENCES clients(id),
    archived INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    project_id TEXT NOT NULL REFERENCES projects(id),
    code TEXT,
    tags TEXT NOT NULL DEFAULT '[]',
    keywords TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    archived INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS entry_events (
    id TEXT PRIMARY KEY,
    ts TEXT NOT NULL,
    task_id TEXT REFERENCES tasks(id),
    subtask_id TEXT REFERENCES tasks(id),
    source TEXT,
    match_source TEXT,
    matched_keyword TEXT,
    calendar_event_id TEXT,
    note TEXT
);

CREATE INDEX IF NOT EXISTS entry_events_ts_idx ON entry_events(ts);
CREATE INDEX IF NOT EXISTS entry_events_task_ts_idx ON entry_events(task_id, ts);
"""


def connect(database_path: Path | str) -> sqlite3.Connection:
    conn = sqlite3.connect(str(database_path))
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL)
