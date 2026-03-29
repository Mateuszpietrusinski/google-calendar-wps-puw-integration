"""Structured logging for ahe-sync.

Format: [YYYY-MM-DD HH:MM:SS CET] [SOURCE] ✓/✗ message
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import SyncResult

_TZ = ZoneInfo("Europe/Warsaw")


def _ts() -> str:
    return datetime.now(_TZ).strftime("%Y-%m-%d %H:%M:%S CET")


def log_sync_result(result: "SyncResult") -> None:
    source = result.source.upper()
    if result.errors:
        for err in result.errors:
            print(f"[{_ts()}] [{source}] \u2717 {err}", flush=True)
    summary = f"{result.created} created, {result.updated} updated, {result.deleted} deleted"
    icon = "\u2713" if not result.errors else "\u2717"
    print(f"[{_ts()}] [{source}] {icon} {summary}", flush=True)


def log_auth_error(source: str, detail: str) -> None:
    source = source.upper()
    print(
        f"[{_ts()}] [{source}] \u2717 AuthError: {detail}",
        flush=True,
    )


def log_network_error(source: str, detail: str) -> None:
    source = source.upper()
    print(
        f"[{_ts()}] [{source}] \u2717 NetworkError: {detail} — sync skipped, will retry at next scheduled time",
        flush=True,
    )


def log_daemon_started(puw_interval: int | None, wps_times: list[tuple[int, int]] | None) -> None:
    parts = []
    if puw_interval is not None:
        parts.append(f"PUW: every {puw_interval} min")
    if wps_times:
        times_str = ", ".join(f"{h:02d}:{m:02d}" for h, m in wps_times)
        parts.append(f"WPS: {times_str} CET")
    detail = " | ".join(parts) if parts else "no connectors enabled"
    print(f"[{_ts()}] [DAEMON] Started. {detail}", flush=True)


def log_daemon_stopped() -> None:
    print(f"[{_ts()}] [DAEMON] Stopped.", flush=True)


def log_remove_result(source: str, count: int) -> None:
    print(f"[{_ts()}] [REMOVE] [{source.upper()}] {count} future events deleted", flush=True)
