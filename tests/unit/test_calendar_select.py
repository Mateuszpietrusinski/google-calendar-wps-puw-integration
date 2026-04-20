"""Unit tests for ahe_sync/google/calendar_select.py."""

import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

from ahe_sync.google.calendar_select import list_calendars, resolve_calendar_id


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_cal(cal_id, summary, access_role="owner", primary=False):
    return {"id": cal_id, "summary": summary, "accessRole": access_role, "primary": primary}


def _make_service(items):
    service = MagicMock()
    service.calendarList().list().execute.return_value = {"items": items}
    return service


def _make_config(calendar_id=""):
    cfg = MagicMock()
    cfg.google_calendar_id = calendar_id
    return cfg


# ── list_calendars ────────────────────────────────────────────────────────────

def test_list_calendars_filters_to_writable():
    items = [
        _make_cal("owner@g", "Owned", access_role="owner"),
        _make_cal("write@g", "Writable", access_role="writer"),
        _make_cal("read@g", "Read-only", access_role="reader"),
        _make_cal("freebusy@g", "Free/Busy", access_role="freeBusyReader"),
    ]
    creds = MagicMock()
    with patch("ahe_sync.google.calendar_select.build", return_value=_make_service(items)):
        result = list_calendars(creds)

    ids = [c["id"] for c in result]
    assert "owner@g" in ids
    assert "write@g" in ids
    assert "read@g" not in ids
    assert "freebusy@g" not in ids


def test_list_calendars_primary_sorted_first():
    items = [
        _make_cal("zzz@g", "Zzz Calendar", access_role="owner"),
        _make_cal("aaa@g", "Aaa Calendar", access_role="owner"),
        _make_cal("pri@g", "Primary", access_role="owner", primary=True),
    ]
    creds = MagicMock()
    with patch("ahe_sync.google.calendar_select.build", return_value=_make_service(items)):
        result = list_calendars(creds)

    assert result[0]["id"] == "pri@g"
    assert result[1]["id"] == "aaa@g"
    assert result[2]["id"] == "zzz@g"


def test_list_calendars_caps_at_20():
    items = [_make_cal(f"cal{i}@g", f"Cal {i:02d}", access_role="owner") for i in range(30)]
    creds = MagicMock()
    with patch("ahe_sync.google.calendar_select.build", return_value=_make_service(items)):
        result = list_calendars(creds)

    assert len(result) == 20


def test_list_calendars_empty_returns_empty():
    creds = MagicMock()
    with patch("ahe_sync.google.calendar_select.build", return_value=_make_service([])):
        result = list_calendars(creds)

    assert result == []


# ── resolve_calendar_id ───────────────────────────────────────────────────────

def test_resolve_uses_env_var_when_set(tmp_path):
    items = [_make_cal("work@g", "Work", access_role="owner")]
    creds = MagicMock()
    config = _make_config(calendar_id="work@g")

    with patch("ahe_sync.google.calendar_select.build", return_value=_make_service(items)), \
         patch("ahe_sync.google.calendar_select.PREFS_PATH", tmp_path / "prefs.json"), \
         patch("ahe_sync.google.calendar_select.load_prefs", return_value={}), \
         patch("ahe_sync.google.calendar_select.save_prefs"):
        result = resolve_calendar_id(config, creds)

    assert result == "work@g"


def test_resolve_env_var_primary_skips_validation(tmp_path):
    items = []  # "primary" not in list — should still be accepted
    creds = MagicMock()
    config = _make_config(calendar_id="primary")

    with patch("ahe_sync.google.calendar_select.build", return_value=_make_service(items)), \
         patch("ahe_sync.google.calendar_select.load_prefs", return_value={}), \
         patch("ahe_sync.google.calendar_select.save_prefs"):
        result = resolve_calendar_id(config, creds)

    assert result == "primary"


def test_resolve_env_var_invalid_id_exits(tmp_path, capsys):
    items = [_make_cal("real@g", "Real", access_role="owner")]
    creds = MagicMock()
    config = _make_config(calendar_id="nonexistent@g")

    with patch("ahe_sync.google.calendar_select.build", return_value=_make_service(items)), \
         patch("ahe_sync.google.calendar_select.load_prefs", return_value={}), \
         pytest.raises(SystemExit):
        resolve_calendar_id(config, creds)

    captured = capsys.readouterr()
    assert "not found or not accessible" in captured.out


def test_resolve_uses_persisted_calendar_id():
    creds = MagicMock()
    config = _make_config(calendar_id="")

    with patch("ahe_sync.google.calendar_select.load_prefs", return_value={"calendar_id": "saved@g"}):
        result = resolve_calendar_id(config, creds)

    assert result == "saved@g"


def test_resolve_interactive_valid_input(monkeypatch, tmp_path):
    items = [
        _make_cal("pri@g", "Primary", access_role="owner", primary=True),
        _make_cal("uni@g", "University", access_role="owner"),
    ]
    creds = MagicMock()
    config = _make_config(calendar_id="")

    monkeypatch.setattr("sys.stdin", MagicMock(isatty=lambda: True))
    monkeypatch.setattr("builtins.input", lambda _: "2")

    saved = {}

    def fake_save(prefs):
        saved.update(prefs)

    with patch("ahe_sync.google.calendar_select.build", return_value=_make_service(items)), \
         patch("ahe_sync.google.calendar_select.load_prefs", return_value={}), \
         patch("ahe_sync.google.calendar_select.save_prefs", side_effect=fake_save):
        result = resolve_calendar_id(config, creds)

    assert result == "uni@g"
    assert saved.get("calendar_id") == "uni@g"


def test_resolve_non_tty_exits_with_error(monkeypatch, capsys):
    creds = MagicMock()
    config = _make_config(calendar_id="")
    items = [_make_cal("cal@g", "Some Cal", access_role="owner")]

    monkeypatch.setattr("sys.stdin", MagicMock(isatty=lambda: False))

    with patch("ahe_sync.google.calendar_select.build", return_value=_make_service(items)), \
         patch("ahe_sync.google.calendar_select.load_prefs", return_value={}), \
         pytest.raises(SystemExit):
        resolve_calendar_id(config, creds)

    captured = capsys.readouterr()
    assert "GOOGLE_CALENDAR_ID" in captured.out


def test_resolve_no_writable_calendars_exits(monkeypatch, capsys):
    creds = MagicMock()
    config = _make_config(calendar_id="")
    items = [_make_cal("read@g", "Read Only", access_role="reader")]

    monkeypatch.setattr("sys.stdin", MagicMock(isatty=lambda: True))

    with patch("ahe_sync.google.calendar_select.build", return_value=_make_service(items)), \
         patch("ahe_sync.google.calendar_select.load_prefs", return_value={}), \
         pytest.raises(SystemExit):
        resolve_calendar_id(config, creds)

    captured = capsys.readouterr()
    assert "No writable" in captured.out
