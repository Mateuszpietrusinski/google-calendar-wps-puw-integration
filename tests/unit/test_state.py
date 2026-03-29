"""Unit tests for ahe_sync/state.py."""

import json
import pytest
from pathlib import Path

from ahe_sync.state import StateStore


def test_load_nonexistent_returns_empty(tmp_path):
    store = StateStore(state_path=tmp_path / "state.json")
    assert store.load("puw") == {}


def test_save_and_load_round_trip(tmp_path):
    store = StateStore(state_path=tmp_path / "state.json")
    puw_state = {"1001": {"gcal_event_id": "abc", "timemodified": 1000}}
    store.save("puw", puw_state)
    assert store.load("puw") == puw_state


def test_save_preserves_other_sources(tmp_path):
    store = StateStore(state_path=tmp_path / "state.json")
    store.save("puw", {"1001": {"gcal_event_id": "abc", "timemodified": 1000}})
    store.save("wps", {"9876": {"gcal_event_id": "def", "checksum": "xyz"}})
    assert store.load("puw")["1001"]["gcal_event_id"] == "abc"
    assert store.load("wps")["9876"]["checksum"] == "xyz"


def test_clear_source_removes_only_that_source(tmp_path):
    store = StateStore(state_path=tmp_path / "state.json")
    store.save("puw", {"1001": {"gcal_event_id": "abc", "timemodified": 1000}})
    store.save("wps", {"9876": {"gcal_event_id": "def", "checksum": "xyz"}})
    store.clear_source("puw")
    assert store.load("puw") == {}
    assert store.load("wps")["9876"]["gcal_event_id"] == "def"


def test_atomic_write_leaves_state_intact_on_interrupted_tmp(tmp_path):
    """If .tmp file exists but os.replace() never ran, original state is intact."""
    state_path = tmp_path / "state.json"
    store = StateStore(state_path=state_path)
    original = {"1001": {"gcal_event_id": "abc", "timemodified": 1000}}
    store.save("puw", original)

    # Simulate a leftover .tmp from a previous crash
    tmp_path_file = state_path.with_suffix(".tmp")
    tmp_path_file.write_text('{"corrupted": true}')

    # The original state.json should still be intact
    assert store.load("puw") == original


def test_save_creates_directory(tmp_path):
    nested = tmp_path / "nested" / "dir" / "state.json"
    store = StateStore(state_path=nested)
    store.save("puw", {"1001": {"gcal_event_id": "abc", "timemodified": 1}})
    assert nested.exists()
