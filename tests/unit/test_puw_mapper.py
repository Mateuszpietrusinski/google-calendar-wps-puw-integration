"""Unit tests for PUW connector event mapping."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from ahe_sync.connectors.puw import PuwConnector


def _make_connector():
    cfg = MagicMock()
    cfg.puw_username = "user"
    cfg.puw_password = "pass"
    return PuwConnector(cfg)


def _raw_event(**kwargs) -> dict:
    base = {
        "id": 1001,
        "eventtype": "meeting_start",
        "modulename": "clickmeeting",
        "timestart": 1743843600,   # 2026-04-05 10:00 UTC
        "timeduration": 5400,      # 90 minutes
        "timemodified": 1000,
        "course": {"fullname": "Bazy Danych"},
        "activityname": "Wykład 1",
        "activitystr": "Lecture description",
        "viewurl": "https://platforma.ahe.lodz.pl/mod/url/1",
    }
    base.update(kwargs)
    return base


# ── event type mapping ────────────────────────────────────────────────────────

def test_meeting_start_is_timed_event():
    connector = _make_connector()
    raw = _raw_event(eventtype="meeting_start", timeduration=5400)
    event = connector._map_event(raw)
    assert event is not None
    assert not event.all_day
    assert event.end > event.start


def test_due_event_is_all_day():
    connector = _make_connector()
    raw = _raw_event(eventtype="due", modulename="assign", timeduration=0)
    event = connector._map_event(raw)
    assert event is not None
    assert event.all_day


def test_attendance_is_skipped():
    connector = _make_connector()
    raw = _raw_event(eventtype="attendance")
    event = connector._map_event(raw)
    assert event is None


def test_zero_duration_event_has_equal_start_end():
    connector = _make_connector()
    raw = _raw_event(eventtype="open", modulename="quiz", timeduration=0)
    event = connector._map_event(raw)
    assert event is not None
    assert event.start == event.end


# ── title construction ────────────────────────────────────────────────────────

def test_title_constructed_as_course_dash_activity():
    connector = _make_connector()
    raw = _raw_event(
        course={"fullname": "Bazy Danych"},
        activityname="Wykład 1",
    )
    event = connector._map_event(raw)
    assert event.title == "Bazy Danych — Wykład 1"


def test_title_fallback_to_course_name_when_no_activity():
    connector = _make_connector()
    raw = _raw_event(activityname="")
    event = connector._map_event(raw)
    assert event.title == "Bazy Danych"


# ── source_id and timemodified ────────────────────────────────────────────────

def test_source_id_is_string_of_moodle_id():
    connector = _make_connector()
    raw = _raw_event(id=1234)
    event = connector._map_event(raw)
    assert event.source_id == "1234"


def test_timemodified_preserved():
    connector = _make_connector()
    raw = _raw_event(timemodified=9999)
    event = connector._map_event(raw)
    assert event.timemodified == 9999


# ── description ──────────────────────────────────────────────────────────────

def test_description_includes_viewurl():
    connector = _make_connector()
    raw = _raw_event(viewurl="https://platforma.ahe.lodz.pl/mod/url/1")
    event = connector._map_event(raw)
    assert "https://platforma.ahe.lodz.pl/mod/url/1" in event.description
