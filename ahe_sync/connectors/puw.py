"""PUW (Moodle) connector.

Authentication: POST /login/token.php → wstoken
Data fetch:     POST core_calendar_get_calendar_monthly_view (3 months)
Change detect:  MoodleCalendarEvent.timemodified (epoch seconds)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, TYPE_CHECKING

import requests

from .base import ConnectorBase
from ..models import CalendarEvent

if TYPE_CHECKING:
    from ..config import Config

logger = logging.getLogger(__name__)

_PUW_BASE = "https://platforma.ahe.lodz.pl"
_SKIPPED_EVENT_TYPES = {"attendance"}


class PuwConnector(ConnectorBase):
    def __init__(self, config: "Config") -> None:
        self._config = config
        self._wstoken: str | None = None
        self._privatetoken: str | None = None

    def _authenticate(self) -> None:
        resp = requests.post(
            f"{_PUW_BASE}/login/token.php",
            params={
                "username": self._config.puw_username,
                "password": self._config.puw_password,
                "service": "moodle_mobile_app",
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise RuntimeError(
                f"AuthError: PUW login failed — check PUW_USERNAME / PUW_PASSWORD in .env "
                f"(Moodle error: {data.get('error')})"
            )
        self._wstoken = data["token"]
        self._privatetoken = data.get("privatetoken")

    def _ensure_authenticated(self) -> None:
        if not self._wstoken:
            self._authenticate()

    def _reauth_with_private_token(self) -> bool:
        """Attempt silent re-auth using privatetoken. Returns True if successful."""
        if not self._privatetoken:
            return False
        try:
            resp = requests.post(
                f"{_PUW_BASE}/login/token.php",
                params={
                    "username": self._config.puw_username,
                    "password": self._config.puw_password,
                    "service": "moodle_mobile_app",
                    "privatetoken": self._privatetoken,
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            if "token" in data:
                self._wstoken = data["token"]
                return True
        except Exception:
            pass
        return False

    def _call_moodle(self, wsfunction: str, params: dict) -> Any:
        """Call a Moodle web service function, retrying once on token rejection."""
        self._ensure_authenticated()
        for attempt in range(2):
            resp = requests.post(
                f"{_PUW_BASE}/webservice/rest/server.php",
                params={
                    "wstoken": self._wstoken,
                    "wsfunction": wsfunction,
                    "moodlewsrestformat": "json",
                    **params,
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, dict) and data.get("errorcode") in ("invalidtoken", "accessexception"):
                if attempt == 0 and self._reauth_with_private_token():
                    continue
                raise RuntimeError(
                    "AuthError: PUW wstoken rejected — check PUW_USERNAME / PUW_PASSWORD in .env"
                )
            return data
        return None  # unreachable

    def fetch(self) -> list[CalendarEvent]:
        now = datetime.now(tz=timezone.utc)
        events: list[CalendarEvent] = []
        for month_offset in range(3):
            target = now + timedelta(days=30 * month_offset)
            try:
                data = self._call_moodle(
                    "core_calendar_get_calendar_monthly_view",
                    {"year": target.year, "month": target.month},
                )
                events.extend(self._parse_month(data))
            except Exception as exc:
                logger.error("PUW fetch error for month +%d: %s", month_offset, exc)
                raise
        return events

    def _parse_month(self, data: dict) -> list[CalendarEvent]:
        events = []
        for week in data.get("weeks", []):
            for day in week.get("days", []):
                for raw in day.get("events", []):
                    event = self._map_event(raw)
                    if event is not None:
                        events.append(event)
        return events

    def _map_event(self, raw: dict) -> CalendarEvent | None:
        eventtype = raw.get("eventtype", "")
        if eventtype in _SKIPPED_EVENT_TYPES:
            return None

        source_id = str(raw["id"])
        timestart = raw["timestart"]
        timeduration = raw.get("timeduration", 0)
        timemodified = raw.get("timemodified", 0)

        course = raw.get("course") or {}
        course_name = course.get("fullname", "")
        activity_name = raw.get("activityname", "")
        title = f"{course_name} — {activity_name}" if activity_name else course_name

        description_parts = []
        if raw.get("activitystr"):
            description_parts.append(raw["activitystr"])
        if raw.get("viewurl"):
            description_parts.append(raw["viewurl"])
        description = "\n".join(description_parts)

        start_dt = datetime.fromtimestamp(timestart, tz=timezone.utc)
        end_dt = datetime.fromtimestamp(timestart + timeduration, tz=timezone.utc)
        all_day = eventtype == "due"

        return CalendarEvent(
            source="puw",
            source_id=source_id,
            title=title,
            description=description,
            start=start_dt,
            end=end_dt,
            all_day=all_day,
            timemodified=timemodified,
        )
