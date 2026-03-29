"""Unit tests for WPS connector mapping and checksum."""

from unittest.mock import MagicMock

import pytest

from ahe_sync.connectors.wps import WpsConnector, _compute_checksum


def _make_connector():
    cfg = MagicMock()
    cfg.wps_username = "user"
    cfg.wps_password = "pass"
    cfg.wps_semester_from = "2026-02-01"
    cfg.wps_semester_to = "2026-06-30"
    return WpsConnector(cfg)


def _raw_entry(**kwargs) -> dict:
    base = {
        "IDPlanZajecPoz": 9876,
        "PNazwa": "Programowanie obiektowe 1",
        "TypZajec": "Laboratorium",
        "DataOD": "2026-04-05T10:00:00",
        "DataDO": "2026-04-05T11:30:00",
        "SalaNumer": "101",
        "SalaAdres": "ul. Sterlinga 26",
        "Webinar": False,
        "Dydaktyk": [{"ImieNazwisko": "dr Kowalski"}],
        "NazwaGrupy": "",
    }
    base.update(kwargs)
    return base


# ── title construction ────────────────────────────────────────────────────────

def test_title_constructed_as_nazwa_dash_typ():
    connector = _make_connector()
    event = connector._map_entry(_raw_entry())
    assert event.title == "Programowanie obiektowe 1 — Laboratorium"


def test_title_fallback_when_no_typ():
    connector = _make_connector()
    event = connector._map_entry(_raw_entry(TypZajec=""))
    assert event.title == "Programowanie obiektowe 1"


# ── on-site vs webinar description ───────────────────────────────────────────

def test_onsite_event_includes_room_and_address():
    connector = _make_connector()
    event = connector._map_entry(_raw_entry(Webinar=False, SalaNumer="101", SalaAdres="ul. Sterlinga 26"))
    assert "101" in event.description
    assert "ul. Sterlinga 26" in event.description


def test_webinar_event_shows_online_webinar():
    connector = _make_connector()
    event = connector._map_entry(_raw_entry(Webinar=True, SalaNumer=None, SalaAdres=None))
    assert "Online (Webinar)" in event.description
    assert "101" not in event.description


def test_teachers_included_in_description():
    connector = _make_connector()
    event = connector._map_entry(_raw_entry(Dydaktyk=[{"ImieNazwisko": "dr Kowalski"}]))
    assert "dr Kowalski" in event.description


# ── source_id ─────────────────────────────────────────────────────────────────

def test_source_id_is_string_of_plan_id():
    connector = _make_connector()
    event = connector._map_entry(_raw_entry(IDPlanZajecPoz=9876))
    assert event.source_id == "9876"


# ── checksum ──────────────────────────────────────────────────────────────────

def test_checksum_changes_on_room_change():
    raw1 = _raw_entry(SalaNumer="101")
    raw2 = _raw_entry(SalaNumer="203")
    assert _compute_checksum(raw1) != _compute_checksum(raw2)


def test_checksum_changes_on_time_change():
    raw1 = _raw_entry(DataOD="2026-04-05T10:00:00")
    raw2 = _raw_entry(DataOD="2026-04-05T11:00:00")
    assert _compute_checksum(raw1) != _compute_checksum(raw2)


def test_checksum_changes_on_teacher_change():
    raw1 = _raw_entry(Dydaktyk=[{"ImieNazwisko": "dr Kowalski"}])
    raw2 = _raw_entry(Dydaktyk=[{"ImieNazwisko": "dr Nowak"}])
    assert _compute_checksum(raw1) != _compute_checksum(raw2)


def test_checksum_stable_when_fields_unchanged():
    raw = _raw_entry()
    assert _compute_checksum(raw) == _compute_checksum(raw)
