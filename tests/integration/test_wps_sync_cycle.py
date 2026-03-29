"""Integration test: full WPS sync cycle with fixture data and mocked CalendarClient."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from ahe_sync.connectors.wps import _compute_checksum
from ahe_sync.models import CalendarEvent
from ahe_sync.state import StateStore
from ahe_sync.sync_engine import apply_sync_plan, compute_diff


def _wps_event(source_id: str, checksum: str = "abc123") -> CalendarEvent:
    now = datetime(2026, 4, 5, 10, 0, tzinfo=timezone.utc)
    return CalendarEvent(
        source="wps",
        source_id=source_id,
        title="Programowanie obiektowe 1 — Laboratorium",
        description="Sala: 101, ul. Sterlinga 26\ndr Kowalski",
        start=now,
        end=datetime(2026, 4, 5, 11, 30, tzinfo=timezone.utc),
        checksum=checksum,
    )


def _make_calendar():
    cal = MagicMock()
    cal.find_tagged_events.return_value = None
    cal.create_event.return_value = "gcal-wps-1"
    return cal


def test_wps_first_sync_creates_events(tmp_path):
    store = StateStore(state_path=tmp_path / "state.json")
    cal = _make_calendar()
    fetched = [_wps_event("9876"), _wps_event("9877")]

    plan = compute_diff(fetched, state={})
    result = apply_sync_plan(plan, cal, store, source="wps")

    assert result.created == 2
    saved = store.load("wps")
    assert "9876" in saved
    assert "9877" in saved


def test_wps_update_on_checksum_change(tmp_path):
    store = StateStore(state_path=tmp_path / "state.json")
    store.save("wps", {"9876": {"gcal_event_id": "gcal-w", "checksum": "old-checksum"}})
    cal = _make_calendar()

    fetched = [_wps_event("9876", checksum="new-checksum")]
    plan = compute_diff(fetched, state=store.load("wps"))
    result = apply_sync_plan(plan, cal, store, source="wps")

    assert result.updated == 1
    cal.update_event.assert_called_once_with("gcal-w", fetched[0])


def test_wps_no_update_when_checksum_unchanged(tmp_path):
    store = StateStore(state_path=tmp_path / "state.json")
    store.save("wps", {"9876": {"gcal_event_id": "gcal-w", "checksum": "same"}})
    cal = _make_calendar()

    fetched = [_wps_event("9876", checksum="same")]
    plan = compute_diff(fetched, state=store.load("wps"))
    result = apply_sync_plan(plan, cal, store, source="wps")

    assert result.created == 0
    assert result.updated == 0
    cal.update_event.assert_not_called()
