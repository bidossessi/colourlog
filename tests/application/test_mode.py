# SPDX-License-Identifier: GPL-3.0-or-later
from colourlog.application.usecases.mode import GetMode, SetMode
from colourlog.domain.value_objects import Mode

from tests.application.fakes import InMemoryModeRepository


class TestGetMode:
    def test_default_manual(self):
        repo = InMemoryModeRepository()
        assert GetMode(modes=repo).execute() is Mode.MANUAL

    def test_reflects_set(self):
        repo = InMemoryModeRepository()
        repo.set(Mode.AUTO)
        assert GetMode(modes=repo).execute() is Mode.AUTO


class TestSetMode:
    def test_set_auto(self):
        repo = InMemoryModeRepository()
        result = SetMode(modes=repo).execute(mode=Mode.AUTO)
        assert result is Mode.AUTO
        assert repo.get() is Mode.AUTO

    def test_set_manual(self):
        repo = InMemoryModeRepository(initial=Mode.AUTO)
        SetMode(modes=repo).execute(mode=Mode.MANUAL)
        assert repo.get() is Mode.MANUAL
