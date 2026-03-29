"""WPS connector.

Authentication: POST /api/Profil/zaloguj → JWT bearer; StudentID from JWT payload
Data fetch:     GET /api/PlanyZajec/GETPlanSzczegolowy
Change detect:  MD5 of mutable fields (DataOD, DataDO, SalaNumer, SalaAdres, teachers)
JWT refresh:    Proactive — re-auth when exp - now < 5 minutes
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import time as time_module
from datetime import datetime, timezone
from typing import Any, TYPE_CHECKING

import requests

from .base import ConnectorBase
from ..models import CalendarEvent

if TYPE_CHECKING:
    from ..config import Config

logger = logging.getLogger(__name__)

_WPS_BASE = "https://wpsapi.ahe.lodz.pl"
_JWT_REFRESH_BUFFER_SECONDS = 300  # re-auth 5 minutes before expiry


def _json_or_raise(resp: requests.Response) -> Any:
    """Raise on HTTP error, then parse JSON — or raise with the raw body on parse failure."""
    resp.raise_for_status()
    try:
        return resp.json()
    except Exception:
        preview = resp.text[:300] if resp.text else "<empty body>"
        raise RuntimeError(
            f"WPS API returned non-JSON (HTTP {resp.status_code}, {resp.request.body}): {preview}"
        )


class WpsConnector(ConnectorBase):
    def __init__(self, config: "Config") -> None:
        self._config = config
        self._token: str | None = None
        self._student_id: str | None = None
        self._token_exp: int = 0
        self._semester_from: str | None = config.wps_semester_from or None
        self._semester_to: str | None = config.wps_semester_to or None

    def _authenticate(self) -> None:
        resp = requests.post(
            f"{_WPS_BASE}/api/Profil/zaloguj",
            data={
                "username": self._config.wps_username,
                "password": self._config.wps_password,
                "roleID": 2,
                "grant_type": "password",
            },
            timeout=30,
        )
        data = _json_or_raise(resp)
        self._token = data["access_token"]
        payload = _decode_jwt_payload(self._token)
        self._student_id = str(payload["id"])
        self._token_exp = int(payload.get("exp", 0))

    def _ensure_fresh_token(self) -> None:
        now = int(time_module.time())
        if not self._token or (self._token_exp and self._token_exp - now < _JWT_REFRESH_BUFFER_SECONDS):
            self._authenticate()

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._token}"}

    def fetch(self) -> list[CalendarEvent]:
        self._ensure_fresh_token()

        # Auto-detect semester bounds if not overridden
        if not self._semester_from or not self._semester_to:
            self._detect_semester_bounds()

        resp = requests.get(
            f"{_WPS_BASE}/api/PlanyZajec/GETPlanSzczegolowy",
            headers=self._headers(),
            params={
                "CzyNieaktywnePlany": "0",
                "DataOd": self._semester_from,
                "DataDo": self._semester_to,
                "StudentID": self._student_id,
                "loader": "none",
            },
            timeout=30,
        )
        if resp.status_code == 401:
            raise RuntimeError(
                "AuthError: WPS login failed — check WPS_USERNAME / WPS_PASSWORD in .env"
            )
        entries = _json_or_raise(resp)
        return [self._map_entry(e) for e in entries]

    def _detect_semester_bounds(self) -> None:
        """Fetch plan without bounds to discover the current semester date range."""
        resp = requests.get(
            f"{_WPS_BASE}/api/PlanyZajec/GETPlanSzczegolowy",
            headers=self._headers(),
            params={
                "CzyNieaktywnePlany": "0",
                "StudentID": self._student_id,
                "loader": "none",
            },
            timeout=30,
        )
        entries = _json_or_raise(resp)
        if not entries:
            # Fallback: use current year as bounds
            year = datetime.now().year
            self._semester_from = f"{year}-01-01"
            self._semester_to = f"{year}-12-31"
            return
        dates_from = [e["DataOD"] for e in entries if e.get("DataOD")]
        dates_to = [e["DataDO"] for e in entries if e.get("DataDO")]
        if dates_from and dates_to:
            self._semester_from = min(dates_from)[:10]
            self._semester_to = max(dates_to)[:10]

    def _map_entry(self, raw: dict) -> CalendarEvent:
        source_id = str(raw["IDPlanZajecPoz"])
        nazwa = raw.get("PNazwa", "")
        typ = raw.get("TypZajec", "")
        title = f"{nazwa} — {typ}" if typ else nazwa

        webinar = raw.get("Webinar", False)
        teachers = ", ".join(
            d["ImieNazwisko"] for d in raw.get("Dydaktyk", []) if d.get("ImieNazwisko")
        )
        if webinar:
            description = "Online (Webinar)"
        else:
            room = raw.get("SalaNumer", "")
            address = raw.get("SalaAdres", "")
            description = f"Sala: {room}"
            if address:
                description += f", {address}"
        if teachers:
            description += f"\n{teachers}"

        start = _parse_dt(raw["DataOD"])
        end = _parse_dt(raw["DataDO"])
        checksum = _compute_checksum(raw)

        return CalendarEvent(
            source="wps",
            source_id=source_id,
            title=title,
            description=description,
            start=start,
            end=end,
            checksum=checksum,
        )


def _decode_jwt_payload(token: str) -> dict:
    """Decode JWT payload without verification (we trust the server's response)."""
    parts = token.split(".")
    payload_b64 = parts[1]
    # Add padding
    payload_b64 += "=" * (-len(payload_b64) % 4)
    return json.loads(base64.urlsafe_b64decode(payload_b64))


def _parse_dt(dt_str: str) -> datetime:
    """Parse ISO datetime string to timezone-aware datetime (UTC)."""
    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _compute_checksum(raw: dict) -> str:
    """MD5 of mutable fields for change detection."""
    teachers = sorted(
        d.get("ImieNazwisko", "") for d in raw.get("Dydaktyk", [])
    )
    data = (
        str(raw.get("DataOD", ""))
        + str(raw.get("DataDO", ""))
        + str(raw.get("SalaNumer", "") or "")
        + str(raw.get("SalaAdres", "") or "")
        + ",".join(teachers)
    )
    return hashlib.md5(data.encode()).hexdigest()
