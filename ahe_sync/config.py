"""Configuration loading and validation.

Loads .env via python-dotenv and exposes a Config dataclass.
Exits with a clear message if required fields are missing or invalid.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import time
from pathlib import Path

from dotenv import load_dotenv
import os


def _load_env(env_path: Path | None = None) -> None:
    load_dotenv(dotenv_path=env_path, override=False)


def _require(keys: list[str]) -> list[str]:
    """Return keys that are missing (empty string or not set)."""
    return [k for k in keys if not os.getenv(k, "").strip()]


def _parse_wps_times(raw: str) -> list[tuple[int, int]]:
    """Parse 'HH:MM,HH:MM' into [(hour, minute), ...]."""
    times = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        h, m = part.split(":")
        times.append((int(h), int(m)))
    return times


@dataclass
class Config:
    # Google OAuth
    google_client_id: str
    google_client_secret: str
    google_calendar_id: str

    # Token storage
    token_storage: str  # "local" | "memory" | "" (prompt)

    # PUW
    puw_enabled: bool
    puw_username: str
    puw_password: str
    puw_poll_interval_minutes: int

    # WPS
    wps_enabled: bool
    wps_username: str
    wps_password: str
    wps_poll_times: list[tuple[int, int]]  # [(hour, minute), ...]
    wps_semester_from: str  # ISO date string or ""
    wps_semester_to: str    # ISO date string or ""

    # Reminders (minutes before; 0 = no reminder)
    reminder_lecture_minutes: int
    reminder_deadline_minutes: int
    reminder_exam_minutes: int
    reminder_wps_minutes: int

    @classmethod
    def load(cls, env_path: Path | None = None) -> "Config":
        _load_env(env_path)

        missing = _require(["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"])
        if missing:
            print(f"Error: Missing required .env fields: {', '.join(missing)}")
            sys.exit(1)

        puw_username = os.getenv("PUW_USERNAME", "").strip()
        puw_password = os.getenv("PUW_PASSWORD", "").strip()
        puw_enabled = bool(puw_username and puw_password)

        wps_username = os.getenv("WPS_USERNAME", "").strip()
        wps_password = os.getenv("WPS_PASSWORD", "").strip()
        wps_enabled = bool(wps_username and wps_password)

        puw_interval_raw = os.getenv("PUW_POLL_INTERVAL_MINUTES", "10").strip()
        try:
            puw_interval = int(puw_interval_raw)
        except ValueError:
            print(f"Error: PUW_POLL_INTERVAL_MINUTES must be an integer (got '{puw_interval_raw}')")
            sys.exit(1)
        if puw_interval < 10:
            print(f"Error: PUW_POLL_INTERVAL_MINUTES must be ≥ 10 (got {puw_interval})")
            sys.exit(1)

        wps_times_raw = os.getenv("WPS_POLL_TIMES_CET", "12:00,21:00").strip()
        try:
            wps_times = _parse_wps_times(wps_times_raw)
        except (ValueError, IndexError):
            print(f"Error: WPS_POLL_TIMES_CET must be comma-separated HH:MM values (got '{wps_times_raw}')")
            sys.exit(1)

        token_storage = os.getenv("TOKEN_STORAGE", "").strip().lower()
        if token_storage not in ("local", "memory", ""):
            print(f"Error: TOKEN_STORAGE must be 'local', 'memory', or unset (got '{token_storage}')")
            sys.exit(1)

        def _int(key: str, default: int) -> int:
            return int(os.getenv(key, str(default)).strip() or default)

        return cls(
            google_client_id=os.getenv("GOOGLE_CLIENT_ID", "").strip(),
            google_client_secret=os.getenv("GOOGLE_CLIENT_SECRET", "").strip(),
            google_calendar_id=os.getenv("GOOGLE_CALENDAR_ID", "primary").strip(),
            token_storage=token_storage,
            puw_enabled=puw_enabled,
            puw_username=puw_username,
            puw_password=puw_password,
            puw_poll_interval_minutes=puw_interval,
            wps_enabled=wps_enabled,
            wps_username=wps_username,
            wps_password=wps_password,
            wps_poll_times=wps_times,
            wps_semester_from=os.getenv("WPS_SEMESTER_FROM", "").strip(),
            wps_semester_to=os.getenv("WPS_SEMESTER_TO", "").strip(),
            reminder_lecture_minutes=_int("REMINDER_LECTURE_MINUTES", 30),
            reminder_deadline_minutes=_int("REMINDER_DEADLINE_MINUTES", 1440),
            reminder_exam_minutes=_int("REMINDER_EXAM_MINUTES", 60),
            reminder_wps_minutes=_int("REMINDER_WPS_MINUTES", 60),
        )
