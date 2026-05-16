# SPDX-License-Identifier: GPL-3.0-or-later
from colourlog.adapters.override.in_memory import InMemoryOverrideStore
from colourlog.application.ports.override import OverrideContext, OverrideSignals


def test_get_returns_none_initially():
    store = InMemoryOverrideStore()
    assert store.get() is None


def test_set_then_get_returns_stored():
    store = InMemoryOverrideStore()
    ctx = OverrideContext(signals=OverrideSignals(window_keyword="t41875"))
    store.set(ctx)
    assert store.get() == ctx


def test_clear_then_get_returns_none():
    store = InMemoryOverrideStore()
    store.set(OverrideContext(signals=OverrideSignals(window_keyword="t41875")))
    store.clear()
    assert store.get() is None


def test_set_replaces_existing_context():
    store = InMemoryOverrideStore()
    store.set(OverrideContext(signals=OverrideSignals(window_keyword="t41875")))
    second = OverrideContext(signals=OverrideSignals(window_keyword="t41622"))
    store.set(second)
    assert store.get() == second


def test_clear_when_empty_is_idempotent():
    store = InMemoryOverrideStore()
    store.clear()
    store.clear()
    assert store.get() is None
