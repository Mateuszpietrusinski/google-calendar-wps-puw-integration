"""Core sync logic — pure functions, no I/O.

compute_diff:  fetched events + known state  →  SyncPlan
apply_sync_plan: SyncPlan + CalendarClient + StateStore  →  SyncResult
"""

from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from .models import CalendarEvent, SyncPlan, SyncResult

if TYPE_CHECKING:
    from .google.calendar import CalendarClient
    from .state import StateStore

logger = logging.getLogger(__name__)


def compute_diff(
    fetched: list[CalendarEvent],
    state: dict[str, Any],
) -> SyncPlan:
    """Compare fetched events against stored state and return a SyncPlan.

    Pure function — no I/O, no side effects.

    state schema per source:
      { "<source_id>": { "gcal_event_id": "...", "timemodified": int | "checksum": str } }
    """
    plan = SyncPlan()
    fetched_ids = {e.source_id for e in fetched}

    for event in fetched:
        if event.source_id not in state:
            plan.to_create.append(event)
        else:
            stored = state[event.source_id]
            if _has_changed(event, stored):
                plan.to_update.append((event, stored["gcal_event_id"]))
            # else: unchanged — skip

    # Deletions: in state but not in fetched
    for source_id, stored in state.items():
        if source_id not in fetched_ids:
            plan.to_delete.append(stored["gcal_event_id"])

    return plan


def _has_changed(event: CalendarEvent, stored: dict[str, Any]) -> bool:
    if event.timemodified is not None:
        return event.timemodified != stored.get("timemodified")
    if event.checksum is not None:
        return event.checksum != stored.get("checksum")
    return False


def apply_sync_plan(
    plan: SyncPlan,
    calendar: "CalendarClient",
    state_store: "StateStore",
    source: str,
) -> SyncResult:
    """Execute a SyncPlan against Google Calendar.

    Per-event isolation: failures are logged and skipped; state is updated
    only for successfully applied operations. Failed events are retried on
    the next sync cycle.
    """
    result = SyncResult(source=source)  # type: ignore[arg-type]
    current_state = state_store.load(source)

    for event in plan.to_create:
        try:
            # Duplicate prevention: check for existing tagged event first
            existing_id = calendar.find_tagged_events(event.source, event.source_id)
            if existing_id:
                # Event exists in Calendar but not in our state — treat as update
                calendar.update_event(existing_id, event)
                current_state[event.source_id] = _make_state_entry(event, existing_id)
                result.updated += 1
            else:
                gcal_id = calendar.create_event(event)
                current_state[event.source_id] = _make_state_entry(event, gcal_id)
                result.created += 1
        except Exception as exc:
            msg = f"Failed to create event '{event.title}' ({event.source_id}): {exc}"
            logger.error(msg)
            result.errors.append(msg)

    for event, gcal_id in plan.to_update:
        try:
            calendar.update_event(gcal_id, event)
            current_state[event.source_id] = _make_state_entry(event, gcal_id)
            result.updated += 1
        except Exception as exc:
            msg = f"Failed to update event '{event.title}' ({event.source_id}): {exc}"
            logger.error(msg)
            result.errors.append(msg)

    for gcal_id in plan.to_delete:
        try:
            calendar.delete_event(gcal_id)
            # Remove from state by gcal_id
            current_state = {
                sid: entry
                for sid, entry in current_state.items()
                if entry.get("gcal_event_id") != gcal_id
            }
            result.deleted += 1
        except Exception as exc:
            msg = f"Failed to delete event (gcal_id={gcal_id}): {exc}"
            logger.error(msg)
            result.errors.append(msg)

    state_store.save(source, current_state)
    return result


def _make_state_entry(event: CalendarEvent, gcal_id: str) -> dict[str, Any]:
    entry: dict[str, Any] = {"gcal_event_id": gcal_id}
    if event.timemodified is not None:
        entry["timemodified"] = event.timemodified
    if event.checksum is not None:
        entry["checksum"] = event.checksum
    return entry
