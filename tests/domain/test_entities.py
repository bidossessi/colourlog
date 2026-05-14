# SPDX-License-Identifier: GPL-3.0-or-later
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from colourlog.domain.entities import Client, Project, Task
from colourlog.domain.exceptions import InvalidKeywordError, InvalidNameError


def _now() -> datetime:
    return datetime(2026, 5, 13, 18, 0, tzinfo=UTC)


class TestClient:
    def test_create_strips_whitespace(self):
        c = Client.create(id=uuid4(), name="  EMSA  ")
        assert c.name == "EMSA"
        assert c.archived is False

    def test_create_empty_name_raises(self):
        with pytest.raises(InvalidNameError):
            Client.create(id=uuid4(), name="   ")

    def test_frozen(self):
        c = Client.create(id=uuid4(), name="EMSA")
        with pytest.raises(FrozenInstanceError):
            c.name = "x"  # type: ignore[misc]

    def test_direct_construct_rejects_untrimmed_name(self):
        with pytest.raises(InvalidNameError):
            Client(id=uuid4(), name=" EMSA")


class TestProject:
    def test_create_optional_client(self):
        p = Project.create(id=uuid4(), name="Evvue")
        assert p.client_id is None

    def test_create_with_client(self):
        cid = uuid4()
        p = Project.create(id=uuid4(), name="Evvue", client_id=cid)
        assert p.client_id == cid

    def test_create_strips_name(self):
        p = Project.create(id=uuid4(), name="  Evvue  ")
        assert p.name == "Evvue"

    def test_direct_construct_rejects_untrimmed_name(self):
        with pytest.raises(InvalidNameError):
            Project(id=uuid4(), name=" Evvue")


class TestTask:
    def test_create_defaults_keywords_to_name_lowercase(self):
        t = Task.create(
            id=uuid4(),
            name="T41622",
            project_id=uuid4(),
            created_at=_now(),
        )
        assert t.keywords == ("t41622",)

    def test_create_explicit_empty_keywords_stays_empty(self):
        t = Task.create(
            id=uuid4(),
            name="T41622",
            project_id=uuid4(),
            created_at=_now(),
            keywords=[],
        )
        assert t.keywords == ()

    def test_create_normalizes_keywords(self):
        t = Task.create(
            id=uuid4(),
            name="T41622",
            project_id=uuid4(),
            created_at=_now(),
            keywords=["  Foo  ", "BAR", "", "   "],
        )
        assert t.keywords == ("foo", "bar")

    def test_direct_construct_rejects_unnormalized_keyword(self):
        with pytest.raises(InvalidKeywordError):
            Task(
                id=uuid4(),
                name="T41622",
                project_id=uuid4(),
                created_at=_now(),
                keywords=("Foo",),
            )

    def test_code_strip_to_value(self):
        t = Task.create(
            id=uuid4(),
            name="T41622",
            project_id=uuid4(),
            created_at=_now(),
            code="  ABC  ",
        )
        assert t.code == "ABC"

    def test_code_empty_becomes_none(self):
        t = Task.create(
            id=uuid4(),
            name="T41622",
            project_id=uuid4(),
            created_at=_now(),
            code="   ",
        )
        assert t.code is None

    def test_tags_stripped_empties_dropped(self):
        t = Task.create(
            id=uuid4(),
            name="T41622",
            project_id=uuid4(),
            created_at=_now(),
            tags=["  meetings  ", "", "billable"],
        )
        assert t.tags == ("meetings", "billable")

    def test_direct_construct_rejects_untrimmed_name(self):
        with pytest.raises(InvalidNameError):
            Task(
                id=uuid4(),
                name=" T41622",
                project_id=uuid4(),
                created_at=_now(),
            )

    def test_created_at_preserved(self):
        ts = _now()
        t = Task.create(
            id=uuid4(),
            name="T41622",
            project_id=uuid4(),
            created_at=ts,
        )
        assert t.created_at == ts
