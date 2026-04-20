"""Calendar selection: list the user's Google Calendars and pick a sync target.

Resolution order:
  1. GOOGLE_CALENDAR_ID in .env (config.google_calendar_id) — skip prompt, verify exists
  2. calendar_id in ~/.config/ahe-sync/prefs.json           — skip prompt, use persisted choice
  3. Interactive numbered list                              — prompt once, persist to prefs.json
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from googleapiclient.discovery import build

from .auth import load_prefs, save_prefs, PREFS_PATH

if TYPE_CHECKING:
    from google.oauth2.credentials import Credentials
    from ..config import Config

_MAX_LISTED = 20


def list_calendars(credentials: "Credentials") -> list[dict]:
    """Return up to 20 writable calendars, primary first then alphabetically.

    Each dict has: id, summary, primary (bool).
    """
    service = build("calendar", "v3", credentials=credentials)
    result = service.calendarList().list().execute()
    items = result.get("items", [])

    writable = [
        c for c in items
        if c.get("accessRole") in ("owner", "writer")
    ]

    writable.sort(key=lambda c: (not c.get("primary", False), c.get("summary", "").lower()))
    return writable[:_MAX_LISTED]


def _select_interactively(credentials: "Credentials") -> str:
    """Display a numbered list and return the chosen calendar ID."""
    if not sys.stdin.isatty():
        print(
            "Calendar selection requires an interactive terminal. "
            "Set GOOGLE_CALENDAR_ID in .env and restart."
        )
        sys.exit(1)

    calendars = list_calendars(credentials)

    if not calendars:
        print(
            "No writable Google Calendars found. "
            "Create a calendar at calendar.google.com and restart."
        )
        sys.exit(1)

    print()
    print("Choose a Google Calendar to sync AHE events into:")
    print()
    for i, cal in enumerate(calendars, start=1):
        label = cal.get("summary", cal["id"])
        tag = " (primary)" if cal.get("primary") else ""
        print(f"  [{i}] {label}{tag}")

    # Show truncation notice if more calendars exist
    service = build("calendar", "v3", credentials=credentials)
    all_items = service.calendarList().list().execute().get("items", [])
    total_writable = sum(
        1 for c in all_items if c.get("accessRole") in ("owner", "writer")
    )
    if total_writable > _MAX_LISTED:
        print(
            f"\n  (Showing {_MAX_LISTED} of {total_writable} calendars. "
            "Set GOOGLE_CALENDAR_ID in .env to use one not listed.)"
        )

    print()
    while True:
        raw = input(f"Enter number [1-{len(calendars)}]: ").strip()
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(calendars):
                return calendars[idx]["id"]
        except ValueError:
            pass
        print(f"  Please enter a number between 1 and {len(calendars)}.")


def resolve_calendar_id(config: "Config", credentials: "Credentials") -> str:
    """Return the target calendar ID, prompting if necessary.

    Side-effect: persists the chosen calendar_id to prefs.json on first selection.
    """
    # 1. Env var present: verify it exists, then use it
    if config.google_calendar_id:
        calendar_id = config.google_calendar_id
        calendars = list_calendars(credentials)
        known_ids = {c["id"] for c in calendars}
        # "primary" is a valid alias the API accepts even if not in the list
        if calendar_id != "primary" and calendar_id not in known_ids:
            print(
                f"GOOGLE_CALENDAR_ID '{calendar_id}' not found or not accessible. "
                "Check your .env."
            )
            sys.exit(1)
        return calendar_id

    # 2. Persisted choice
    prefs = load_prefs()
    if prefs.get("calendar_id"):
        return prefs["calendar_id"]

    # 3. Interactive selection
    calendar_id = _select_interactively(credentials)
    prefs["calendar_id"] = calendar_id
    save_prefs(prefs)
    print(f"\nSyncing to: {calendar_id}")
    print("Tip: Add GOOGLE_CALENDAR_ID to your .env to skip this prompt on future installs.\n")
    return calendar_id
