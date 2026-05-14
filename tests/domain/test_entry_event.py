# SPDX-License-Identifier: GPL-3.0-or-later
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from colourlog.domain import entities, exceptions, value_objects


def _ts() -> datetime:
    return datetime(2026, 5, 14, 10, 0, tzinfo=UTC)


class TestStartEvent:
    def test_manual_no_subtask(self):
        e = entities.EntryEvent.create(
            id=uuid4(),
            ts=_ts(),
            task_id=uuid4(),
            source=value_objects.Source.MANUAL,
        )
        assert e.is_start
        assert not e.is_stop

    def test_auto_window_match(self):
        e = entities.EntryEvent.create(
            id=uuid4(),
            ts=_ts(),
            task_id=uuid4(),
            source=value_objects.Source.AUTO,
            match_source=value_objects.MatchSource.WINDOW,
            matched_keyword="t41622",
        )
        assert e.source is value_objects.Source.AUTO
        assert e.match_source is value_objects.MatchSource.WINDOW

    def test_with_subtask(self):
        t, st = uuid4(), uuid4()
        e = entities.EntryEvent.create(
            id=uuid4(),
            ts=_ts(),
            task_id=t,
            subtask_id=st,
            source=value_objects.Source.MANUAL,
        )
        assert e.subtask_id == st

    def test_text_fields_normalized(self):
        e = entities.EntryEvent.create(
            id=uuid4(),
            ts=_ts(),
            task_id=uuid4(),
            source=value_objects.Source.MANUAL,
            note="  focus  ",
        )
        assert e.note == "focus"

    def test_empty_text_becomes_none(self):
        e = entities.EntryEvent.create(
            id=uuid4(),
            ts=_ts(),
            task_id=uuid4(),
            source=value_objects.Source.MANUAL,
            note="   ",
        )
        assert e.note is None


class TestStopEvent:
    def test_stop_event(self):
        e = entities.EntryEvent.create(id=uuid4(), ts=_ts())
        assert e.is_stop
        assert not e.is_start
        assert e.task_id is None
        assert e.source is None


class TestInvariants:
    def test_naive_ts_raises(self):
        with pytest.raises(exceptions.NaiveDatetimeError):
            entities.EntryEvent(
                id=uuid4(),
                ts=datetime(2026, 5, 14, 10, 0),
            )

    def test_task_without_source_raises(self):
        with pytest.raises(exceptions.IncoherentStopEventError):
            entities.EntryEvent(
                id=uuid4(),
                ts=_ts(),
                task_id=uuid4(),
            )

    def test_source_without_task_raises(self):
        with pytest.raises(exceptions.IncoherentStopEventError):
            entities.EntryEvent(
                id=uuid4(),
                ts=_ts(),
                source=value_objects.Source.MANUAL,
            )

    def test_subtask_without_task_raises(self):
        with pytest.raises(exceptions.SubtaskWithoutTaskError):
            entities.EntryEvent(
                id=uuid4(),
                ts=_ts(),
                subtask_id=uuid4(),
            )

    def test_manual_with_match_source_raises(self):
        with pytest.raises(exceptions.SourceMatchSourceMismatchError):
            entities.EntryEvent(
                id=uuid4(),
                ts=_ts(),
                task_id=uuid4(),
                source=value_objects.Source.MANUAL,
                match_source=value_objects.MatchSource.WINDOW,
            )

    def test_auto_without_match_source_raises(self):
        with pytest.raises(exceptions.SourceMatchSourceMismatchError):
            entities.EntryEvent(
                id=uuid4(),
                ts=_ts(),
                task_id=uuid4(),
                source=value_objects.Source.AUTO,
            )

    def test_direct_construct_rejects_untrimmed_note(self):
        with pytest.raises(exceptions.InvalidTextFieldError):
            entities.EntryEvent(
                id=uuid4(),
                ts=_ts(),
                task_id=uuid4(),
                source=value_objects.Source.MANUAL,
                note=" hi",
            )
