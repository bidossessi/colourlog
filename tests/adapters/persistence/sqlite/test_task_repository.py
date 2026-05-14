# SPDX-License-Identifier: GPL-3.0-or-later
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from colourlog.adapters.persistence.sqlite.project_repository import (
    SqliteProjectRepository,
)
from colourlog.adapters.persistence.sqlite.task_repository import SqliteTaskRepository
from colourlog.domain.entities import Project, Task


def _now() -> datetime:
    return datetime(2026, 5, 13, 18, 0, tzinfo=UTC)


def _seed_project(db_path: Path) -> Project:
    projects = SqliteProjectRepository(db_path)
    p = Project.create(id=uuid4(), name="Evvue")
    projects.add(p)
    return p


def _task(
    project_id: UUID,
    name: str = "T41622",
    code: str | None = "ABC",
    tags: tuple[str, ...] = ("meetings",),
    keywords: tuple[str, ...] | None = None,
    archived: bool = False,
) -> Task:
    return Task.create(
        id=uuid4(),
        name=name,
        project_id=project_id,
        created_at=_now(),
        code=code,
        tags=tags,
        keywords=list(keywords) if keywords is not None else None,
        archived=archived,
    )


class TestSqliteTaskRepository:
    def test_add_then_get_roundtrip_json_and_datetime(self, db_path: Path):
        p = _seed_project(db_path)
        repo = SqliteTaskRepository(db_path)
        t = _task(p.id, keywords=("t41622", "foo"))
        repo.add(t)
        fetched = repo.get(t.id)
        assert fetched == t
        assert fetched is not None
        assert fetched.tags == ("meetings",)
        assert fetched.keywords == ("t41622", "foo")
        assert fetched.created_at == _now()

    def test_get_missing_returns_none(self, db_path: Path):
        assert SqliteTaskRepository(db_path).get(uuid4()) is None

    def test_list_default_excludes_archived(self, db_path: Path):
        p = _seed_project(db_path)
        repo = SqliteTaskRepository(db_path)
        a = _task(p.id, name="A")
        b = _task(p.id, name="B")
        repo.add(a)
        repo.add(b)
        archived = Task.create(
            id=a.id,
            name=a.name,
            project_id=a.project_id,
            created_at=a.created_at,
            code=a.code,
            tags=a.tags,
            keywords=a.keywords,
            archived=True,
        )
        repo.update(archived)
        listed = repo.list()
        assert {t.id for t in listed} == {b.id}

    def test_list_filter_by_project(self, db_path: Path):
        projects = SqliteProjectRepository(db_path)
        p1 = Project.create(id=uuid4(), name="P1")
        p2 = Project.create(id=uuid4(), name="P2")
        projects.add(p1)
        projects.add(p2)
        repo = SqliteTaskRepository(db_path)
        t1 = _task(p1.id, name="X")
        t2 = _task(p2.id, name="Y")
        repo.add(t1)
        repo.add(t2)
        listed = repo.list(project_id=p1.id)
        assert listed == [t1]

    def test_list_include_archived(self, db_path: Path):
        p = _seed_project(db_path)
        repo = SqliteTaskRepository(db_path)
        a = _task(p.id, name="A")
        b = _task(p.id, name="B")
        repo.add(a)
        repo.add(b)
        archived = Task.create(
            id=a.id,
            name=a.name,
            project_id=a.project_id,
            created_at=a.created_at,
            code=a.code,
            tags=a.tags,
            keywords=a.keywords,
            archived=True,
        )
        repo.update(archived)
        listed = repo.list(include_archived=True)
        assert {t.id for t in listed} == {a.id, b.id}

    def test_update_mutates_all_fields(self, db_path: Path):
        p = _seed_project(db_path)
        repo = SqliteTaskRepository(db_path)
        t = _task(p.id, code="OLD")
        repo.add(t)
        updated = Task.create(
            id=t.id,
            name="T-new",
            project_id=t.project_id,
            created_at=t.created_at,
            code="NEW",
            tags=("billable",),
            keywords=["alpha", "beta"],
            archived=True,
        )
        repo.update(updated)
        fetched = repo.get(t.id)
        assert fetched == updated

    def test_delete_removes(self, db_path: Path):
        p = _seed_project(db_path)
        repo = SqliteTaskRepository(db_path)
        t = _task(p.id)
        repo.add(t)
        repo.delete(t.id)
        assert repo.get(t.id) is None
