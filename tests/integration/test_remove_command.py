"""Integration test: remove --source command behaviour."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, call

import pytest

from ahe_sync.__main__ import _run_remove
from ahe_sync.state import StateStore


def _future_event(gcal_id: str) -> dict:
    future = (datetime.now(tz=timezone.utc) + timedelta(days=7)).isoformat()
    return {"id": gcal_id, "start": {"dateTime": future}}


def _past_event(gcal_id: str) -> dict:
    past = (datetime.now(tz=timezone.utc) - timedelta(days=7)).isoformat()
    return {"id": gcal_id, "start": {"dateTime": past}}


def test_remove_puw_deletes_future_events(tmp_path):
    store = StateStore(state_path=tmp_path / "state.json")
    store.save("puw", {
        "1001": {"gcal_event_id": "gcal-future-1", "timemodified": 100},
        "1002": {"gcal_event_id": "gcal-future-2", "timemodified": 100},
    })
    store.save("wps", {"9876": {"gcal_event_id": "gcal-wps", "checksum": "abc"}})

    cal = MagicMock()
    cal.list_future_tagged_events.return_value = [
        _future_event("gcal-future-1"),
        _future_event("gcal-future-2"),
    ]

    _run_remove("puw", cal, store)

    assert cal.delete_event.call_count == 2
    cal.delete_event.assert_any_call("gcal-future-1")
    cal.delete_event.assert_any_call("gcal-future-2")


def test_remove_clears_puw_state_but_not_wps(tmp_path):
    store = StateStore(state_path=tmp_path / "state.json")
    store.save("puw", {"1001": {"gcal_event_id": "gcal-1", "timemodified": 100}})
    store.save("wps", {"9876": {"gcal_event_id": "gcal-wps", "checksum": "abc"}})

    cal = MagicMock()
    cal.list_future_tagged_events.return_value = [_future_event("gcal-1")]

    _run_remove("puw", cal, store)

    assert store.load("puw") == {}
    assert store.load("wps")["9876"]["gcal_event_id"] == "gcal-wps"


def test_remove_does_not_touch_wps_events_when_removing_puw(tmp_path):
    store = StateStore(state_path=tmp_path / "state.json")
    cal = MagicMock()
    cal.list_future_tagged_events.return_value = []

    _run_remove("puw", cal, store)

    # list_future_tagged_events called with "puw", not "wps"
    cal.list_future_tagged_events.assert_called_once_with("puw")
