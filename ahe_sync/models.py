"""Shared dataclasses used across connectors, sync engine, and calendar client."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


@dataclass
class CalendarEvent:
    source: Literal["puw", "wps"]
    source_id: str           # str(MoodleCalendarEvent.id) or str(IDPlanZajecPoz)
    title: str
    description: str
    start: datetime          # timezone-aware (Europe/Warsaw)
    end: datetime            # timezone-aware
    all_day: bool = False
    timemodified: int | None = None  # PUW only: epoch seconds for change detection
    checksum: str | None = None      # WPS only: MD5 of mutable fields


@dataclass
class SyncPlan:
    to_create: list[CalendarEvent] = field(default_factory=list)
    to_update: list[tuple[CalendarEvent, str]] = field(default_factory=list)  # (event, gcal_event_id)
    to_delete: list[str] = field(default_factory=list)  # gcal_event_ids


@dataclass
class SyncResult:
    source: Literal["puw", "wps"]
    created: int = 0
    updated: int = 0
    deleted: int = 0
    errors: list[str] = field(default_factory=list)
