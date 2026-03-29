"""Integration test: full PUW sync cycle with fixture data and mocked CalendarClient."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, call

import pytest

from ahe_sync.connectors.puw import PuwConnector
from ahe_sync.models import CalendarEvent
from ahe_sync.state import StateStore
from ahe_sync.sync_engine import apply_sync_plan, compute_diff


def _make_calendar(find_result=None):
    cal = MagicMock()
    cal.find_tagged_events.return_value = find_result
    cal.create_event.return_value = "gcal-new"
    return cal


def _puw_event(source_id: str, timemodified: int = 100) -> CalendarEvent:
    now = datetime(2026, 4, 1, 10, 0, tzinfo=timezone.utc)
    return CalendarEvent(
        source="puw",
        source_id=source_id,
        title=f"Bazy Danych — Wykład {source_id}",
        description="",
        start=now,
        end=datetime(2026, 4, 1, 11, 30, tzinfo=timezone.utc),
        timemodified=timemodified,
    )


def test_first_sync_creates_all_events(tmp_path):
    store = StateStore(state_path=tmp_path / "state.json")
    cal = _make_calendar(find_result=None)
    fetched = [_puw_event("1001"), _puw_event("1002"), _puw_event("1003")]

    plan = compute_diff(fetched, state={})
    result = apply_sync_plan(plan, cal, store, source="puw")

    assert result.created == 3
    assert result.updated == 0
    assert result.deleted == 0
    assert cal.create_event.call_count == 3

    saved = store.load("puw")
    assert set(saved.keys()) == {"1001", "1002", "1003"}


def test_update_detected_on_timemodified_change(tmp_path):
    store = StateStore(state_path=tmp_path / "state.json")
    store.save("puw", {"1001": {"gcal_event_id": "gcal-1", "timemodified": 50}})
    cal = _make_calendar()

    fetched = [_puw_event("1001", timemodified=100)]
    plan = compute_diff(fetched, state=store.load("puw"))
    result = apply_sync_plan(plan, cal, store, source="puw")

    assert result.updated == 1
    cal.update_event.assert_called_once_with("gcal-1", fetched[0])


def test_cancelled_event_deleted(tmp_path):
    store = StateStore(state_path=tmp_path / "state.json")
    store.save("puw", {"1001": {"gcal_event_id": "gcal-1", "timemodified": 100}})
    cal = _make_calendar()

    plan = compute_diff([], state=store.load("puw"))
    result = apply_sync_plan(plan, cal, store, source="puw")

    assert result.deleted == 1
    cal.delete_event.assert_called_once_with("gcal-1")
    assert store.load("puw") == {}


def test_state_updated_only_for_successful_events(tmp_path):
    store = StateStore(state_path=tmp_path / "state.json")
    cal = _make_calendar(find_result=None)
    cal.create_event.side_effect = ["gcal-ok", Exception("API down")]

    fetched = [_puw_event("1001"), _puw_event("1002")]
    plan = compute_diff(fetched, state={})
    result = apply_sync_plan(plan, cal, store, source="puw")

    assert result.created == 1
    assert len(result.errors) == 1
    saved = store.load("puw")
    assert len(saved) == 1
