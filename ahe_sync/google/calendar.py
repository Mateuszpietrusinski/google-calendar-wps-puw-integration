"""Google Calendar API client.

All events written by this tool carry two privateProperties:
  ahe-sync-source: "puw" | "wps"
  ahe-sync-id:     str(source_event_id)

The client never reads, updates, or deletes events it did not create.
delete_event and update_event only accept explicit gcal_event_ids — no
calendar-wide search by title or time range.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

if TYPE_CHECKING:
    from google.oauth2.credentials import Credentials
    from ..models import CalendarEvent

_TOOL_SOURCE_KEY = "ahe-sync-source"
_TOOL_ID_KEY = "ahe-sync-id"


class CalendarClient:
    def __init__(self, credentials: "Credentials", calendar_id: str = "primary") -> None:
        self._service = build("calendar", "v3", credentials=credentials)
        self._calendar_id = calendar_id

    def create_event(self, event: "CalendarEvent") -> str:
        """Create a Google Calendar event and return its gcal event ID."""
        body = self._to_gcal_body(event)
        result = (
            self._service.events()
            .insert(calendarId=self._calendar_id, body=body)
            .execute()
        )
        return result["id"]

    def update_event(self, gcal_event_id: str, event: "CalendarEvent") -> None:
        """Update an existing Google Calendar event."""
        body = self._to_gcal_body(event)
        (
            self._service.events()
            .update(calendarId=self._calendar_id, eventId=gcal_event_id, body=body)
            .execute()
        )

    def delete_event(self, gcal_event_id: str) -> None:
        """Delete a Google Calendar event by its gcal event ID."""
        (
            self._service.events()
            .delete(calendarId=self._calendar_id, eventId=gcal_event_id)
            .execute()
        )

    def find_tagged_events(self, source: str, source_id: str) -> str | None:
        """Find a tool-created event by its extended properties.

        Returns the gcal_event_id if found, otherwise None.
        Uses privateExtendedProperty filters to avoid touching personal events.
        """
        result = (
            self._service.events()
            .list(
                calendarId=self._calendar_id,
                privateExtendedProperty=[
                    f"{_TOOL_SOURCE_KEY}={source}",
                    f"{_TOOL_ID_KEY}={source_id}",
                ],
                maxResults=1,
            )
            .execute()
        )
        items = result.get("items", [])
        if items:
            return items[0]["id"]
        return None

    def list_future_tagged_events(self, source: str) -> list[dict]:
        """Return all future tool-created events for a given source.

        Used by the remove command to find events to delete.
        """
        now = datetime.now(tz=timezone.utc).isoformat()
        events = []
        page_token = None
        while True:
            result = (
                self._service.events()
                .list(
                    calendarId=self._calendar_id,
                    privateExtendedProperty=f"{_TOOL_SOURCE_KEY}={source}",
                    timeMin=now,
                    singleEvents=True,
                    pageToken=page_token,
                    maxResults=250,
                )
                .execute()
            )
            events.extend(result.get("items", []))
            page_token = result.get("nextPageToken")
            if not page_token:
                break
        return events

    def _to_gcal_body(self, event: "CalendarEvent") -> dict:
        body: dict = {
            "summary": event.title,
            "description": event.description,
            "extendedProperties": {
                "private": {
                    _TOOL_SOURCE_KEY: event.source,
                    _TOOL_ID_KEY: event.source_id,
                }
            },
        }

        if event.all_day:
            body["start"] = {"date": event.start.date().isoformat()}
            body["end"] = {"date": event.end.date().isoformat()}
        else:
            body["start"] = {"dateTime": event.start.isoformat(), "timeZone": "Europe/Warsaw"}
            body["end"] = {"dateTime": event.end.isoformat(), "timeZone": "Europe/Warsaw"}

        return body
