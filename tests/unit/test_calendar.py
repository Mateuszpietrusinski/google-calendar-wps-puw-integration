"""Unit tests for ahe_sync/google/calendar.py."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, call, patch

import pytest

from ahe_sync.models import CalendarEvent
from ahe_sync.google.calendar import CalendarClient, _TOOL_SOURCE_KEY, _TOOL_ID_KEY


def _make_client():
    mock_service = MagicMock()
    with patch("ahe_sync.google.calendar.build", return_value=mock_service):
        client = CalendarClient(credentials=MagicMock(), calendar_id="primary")
    client._service = mock_service
    return client, mock_service


def _timed_event(source="puw", source_id="1001") -> CalendarEvent:
    now = datetime(2026, 4, 1, 10, 0, tzinfo=timezone.utc)
    return CalendarEvent(
        source=source,  # type: ignore[arg-type]
        source_id=source_id,
        title="Bazy Danych — Wykład 1",
        description="Some description",
        start=now,
        end=datetime(2026, 4, 1, 11, 30, tzinfo=timezone.utc),
        all_day=False,
        timemodified=1000,
    )


def _all_day_event() -> CalendarEvent:
    now = datetime(2026, 4, 15, tzinfo=timezone.utc)
    return CalendarEvent(
        source="puw",
        source_id="2001",
        title="Deadline",
        description="Submit by today",
        start=now,
        end=now,
        all_day=True,
    )


# ── create_event ─────────────────────────────────────────────────────────────

def test_create_event_sets_extended_properties():
    client, svc = _make_client()
    svc.events().insert().execute.return_value = {"id": "new-id"}

    event = _timed_event()
    gcal_id = client.create_event(event)

    insert_call = svc.events().insert
    body = insert_call.call_args.kwargs["body"]
    private = body["extendedProperties"]["private"]
    assert private[_TOOL_SOURCE_KEY] == "puw"
    assert private[_TOOL_ID_KEY] == "1001"
    assert gcal_id == "new-id"


def test_create_event_timed_uses_datetime():
    client, svc = _make_client()
    svc.events().insert().execute.return_value = {"id": "x"}

    event = _timed_event()
    client.create_event(event)

    body = svc.events().insert.call_args.kwargs["body"]
    assert "dateTime" in body["start"]
    assert "date" not in body["start"]


def test_create_event_all_day_uses_date():
    client, svc = _make_client()
    svc.events().insert().execute.return_value = {"id": "x"}

    event = _all_day_event()
    client.create_event(event)

    body = svc.events().insert.call_args.kwargs["body"]
    assert "date" in body["start"]
    assert "dateTime" not in body["start"]


# ── find_tagged_events ────────────────────────────────────────────────────────

def test_find_tagged_events_uses_correct_query_params():
    client, svc = _make_client()
    svc.events().list().execute.return_value = {"items": [{"id": "found-id"}]}

    result = client.find_tagged_events("puw", "1001")

    list_call = svc.events().list
    kwargs = list_call.call_args.kwargs
    assert f"{_TOOL_SOURCE_KEY}=puw" in kwargs["privateExtendedProperty"]
    assert f"{_TOOL_ID_KEY}=1001" in kwargs["privateExtendedProperty"]
    assert result == "found-id"


def test_find_tagged_events_returns_none_when_not_found():
    client, svc = _make_client()
    svc.events().list().execute.return_value = {"items": []}

    result = client.find_tagged_events("puw", "9999")

    assert result is None


# ── delete_event ─────────────────────────────────────────────────────────────

def test_delete_event_uses_explicit_gcal_id():
    client, svc = _make_client()

    client.delete_event("explicit-gcal-id")

    delete_call = svc.events().delete
    assert delete_call.call_args.kwargs["eventId"] == "explicit-gcal-id"
    # Verify no list() call was made (no search by title)
    svc.events().list.assert_not_called()
