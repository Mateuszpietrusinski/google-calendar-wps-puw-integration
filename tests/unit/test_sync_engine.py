"""Unit tests for ahe_sync/sync_engine.py."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, call

import pytest

from ahe_sync.models import CalendarEvent, SyncPlan
from ahe_sync.sync_engine import compute_diff, apply_sync_plan


def _event(source_id: str, timemodified: int = 100, source: str = "puw") -> CalendarEvent:
    now = datetime(2026, 4, 1, 10, 0, tzinfo=timezone.utc)
    return CalendarEvent(
        source=source,  # type: ignore[arg-type]
        source_id=source_id,
        title=f"Event {source_id}",
        description="",
        start=now,
        end=now,
        timemodified=timemodified,
    )


def _wps_event(source_id: str, checksum: str = "abc") -> CalendarEvent:
    now = datetime(2026, 4, 1, 10, 0, tzinfo=timezone.utc)
    return CalendarEvent(
        source="wps",
        source_id=source_id,
        title=f"WPS {source_id}",
        description="",
        start=now,
        end=now,
        checksum=checksum,
    )


# ── compute_diff tests ───────────────────────────────────────────────────────

def test_new_event_goes_to_create():
    plan = compute_diff([_event("1001")], state={})
    assert len(plan.to_create) == 1
    assert plan.to_create[0].source_id == "1001"
    assert plan.to_update == []
    assert plan.to_delete == []


def test_changed_event_goes_to_update():
    state = {"1001": {"gcal_event_id": "gcal-abc", "timemodified": 99}}
    plan = compute_diff([_event("1001", timemodified=100)], state=state)
    assert plan.to_create == []
    assert len(plan.to_update) == 1
    assert plan.to_update[0][1] == "gcal-abc"
    assert plan.to_delete == []


def test_unchanged_event_excluded():
    state = {"1001": {"gcal_event_id": "gcal-abc", "timemodified": 100}}
    plan = compute_diff([_event("1001", timemodified=100)], state=state)
    assert plan.to_create == []
    assert plan.to_update == []
    assert plan.to_delete == []


def test_missing_event_goes_to_delete():
    state = {"1001": {"gcal_event_id": "gcal-abc", "timemodified": 100}}
    plan = compute_diff([], state=state)
    assert plan.to_create == []
    assert plan.to_update == []
    assert plan.to_delete == ["gcal-abc"]


def test_mixed_batch():
    state = {
        "1001": {"gcal_event_id": "gcal-1", "timemodified": 100},  # unchanged
        "1002": {"gcal_event_id": "gcal-2", "timemodified": 50},   # changed
        "1003": {"gcal_event_id": "gcal-3", "timemodified": 100},  # deleted
    }
    fetched = [
        _event("1001", timemodified=100),   # unchanged
        _event("1002", timemodified=99),    # updated (different timemodified)
        _event("1004"),                     # new
    ]
    plan = compute_diff(fetched, state=state)
    assert {e.source_id for e in plan.to_create} == {"1004"}
    assert len(plan.to_update) == 1
    assert plan.to_update[0][0].source_id == "1002"
    assert plan.to_delete == ["gcal-3"]


def test_empty_fetched_deletes_all():
    state = {
        "1001": {"gcal_event_id": "gcal-1", "timemodified": 100},
        "1002": {"gcal_event_id": "gcal-2", "timemodified": 200},
    }
    plan = compute_diff([], state=state)
    assert plan.to_create == []
    assert plan.to_update == []
    assert set(plan.to_delete) == {"gcal-1", "gcal-2"}


def test_empty_state_creates_all():
    fetched = [_event("1001"), _event("1002")]
    plan = compute_diff(fetched, state={})
    assert {e.source_id for e in plan.to_create} == {"1001", "1002"}


def test_wps_checksum_change_detected():
    state = {"9876": {"gcal_event_id": "gcal-w", "checksum": "old"}}
    plan = compute_diff([_wps_event("9876", checksum="new")], state=state)
    assert len(plan.to_update) == 1


def test_wps_checksum_unchanged_excluded():
    state = {"9876": {"gcal_event_id": "gcal-w", "checksum": "same"}}
    plan = compute_diff([_wps_event("9876", checksum="same")], state=state)
    assert plan.to_update == []


# ── apply_sync_plan tests ────────────────────────────────────────────────────

def _make_calendar(find_result=None):
    cal = MagicMock()
    cal.find_tagged_events.return_value = find_result
    cal.create_event.return_value = "new-gcal-id"
    return cal


def _make_state_store(initial=None):
    store = MagicMock()
    store.load.return_value = initial or {}
    return store


def test_apply_create_new_event():
    event = _event("1001")
    plan = SyncPlan(to_create=[event])
    cal = _make_calendar(find_result=None)
    store = _make_state_store()

    result = apply_sync_plan(plan, cal, store, source="puw")

    cal.create_event.assert_called_once_with(event)
    assert result.created == 1
    assert result.updated == 0
    store.save.assert_called_once()


def test_apply_update_existing_event():
    event = _event("1001")
    plan = SyncPlan(to_update=[(event, "existing-gcal-id")])
    cal = _make_calendar()
    store = _make_state_store({"1001": {"gcal_event_id": "existing-gcal-id", "timemodified": 50}})

    result = apply_sync_plan(plan, cal, store, source="puw")

    cal.update_event.assert_called_once_with("existing-gcal-id", event)
    assert result.updated == 1


def test_apply_delete_event():
    plan = SyncPlan(to_delete=["gcal-to-delete"])
    cal = _make_calendar()
    store = _make_state_store({"1001": {"gcal_event_id": "gcal-to-delete", "timemodified": 100}})

    result = apply_sync_plan(plan, cal, store, source="puw")

    cal.delete_event.assert_called_once_with("gcal-to-delete")
    assert result.deleted == 1


def test_duplicate_prevention_create_becomes_update():
    """If find_tagged_events returns an ID, create must become an update."""
    event = _event("1001")
    plan = SyncPlan(to_create=[event])
    cal = _make_calendar(find_result="existing-gcal-id")
    store = _make_state_store()

    result = apply_sync_plan(plan, cal, store, source="puw")

    cal.create_event.assert_not_called()
    cal.update_event.assert_called_once_with("existing-gcal-id", event)
    assert result.updated == 1
    assert result.created == 0


def test_partial_failure_isolates_per_event():
    """Failure on one event does not prevent others from being processed."""
    event_ok = _event("1001")
    event_fail = _event("1002")
    plan = SyncPlan(to_create=[event_ok, event_fail])

    cal = _make_calendar(find_result=None)
    cal.create_event.side_effect = [
        "gcal-ok",           # 1001 succeeds
        Exception("API 500"),  # 1002 fails
    ]
    store = _make_state_store()

    result = apply_sync_plan(plan, cal, store, source="puw")

    assert result.created == 1
    assert len(result.errors) == 1
    assert "1002" in result.errors[0]
    # State saved once with only the successful event
    saved_state = store.save.call_args[0][1]
    assert "1001" in saved_state
    assert "1002" not in saved_state
