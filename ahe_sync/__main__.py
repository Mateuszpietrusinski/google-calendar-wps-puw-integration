"""ahe-sync entry point.

Usage:
  python -m ahe_sync                         — start daemon
  python -m ahe_sync remove --source puw    — remove future PUW events
  python -m ahe_sync remove --source wps    — remove future WPS events
"""

from __future__ import annotations

import argparse
import signal
import sys
import time

from .config import Config
from .google.auth import get_valid_credentials
from .google.calendar import CalendarClient
from .connectors.puw import PuwConnector
from .connectors.wps import WpsConnector
from .scheduler import build_scheduler
from .state import StateStore
from .sync_engine import apply_sync_plan, compute_diff
from .observability import (
    log_daemon_started,
    log_daemon_stopped,
    log_sync_result,
    log_auth_error,
    log_network_error,
    log_remove_result,
)


def _make_puw_job(connector: PuwConnector, calendar: CalendarClient, store: StateStore):
    def run():
        try:
            fetched = connector.fetch()
            state = store.load("puw")
            plan = compute_diff(fetched, state)
            result = apply_sync_plan(plan, calendar, store, source="puw")
            log_sync_result(result)
        except RuntimeError as exc:
            if "AuthError" in str(exc):
                log_auth_error("puw", str(exc))
            else:
                log_network_error("puw", str(exc))
        except Exception as exc:
            log_network_error("puw", str(exc))
    return run


def _make_wps_job(connector: WpsConnector, calendar: CalendarClient, store: StateStore):
    def run():
        try:
            fetched = connector.fetch()
            state = store.load("wps")
            plan = compute_diff(fetched, state)
            result = apply_sync_plan(plan, calendar, store, source="wps")
            log_sync_result(result)
        except RuntimeError as exc:
            if "AuthError" in str(exc):
                log_auth_error("wps", str(exc))
            else:
                log_network_error("wps", str(exc))
        except Exception as exc:
            log_network_error("wps", str(exc))
    return run


def _run_remove(source: str, calendar: CalendarClient, store: StateStore) -> None:
    events = calendar.list_future_tagged_events(source)
    for event in events:
        calendar.delete_event(event["id"])
    store.clear_source(source)
    log_remove_result(source, len(events))


def _run_daemon(config: Config) -> None:
    creds = get_valid_credentials(config)
    calendar = CalendarClient(creds, config.google_calendar_id)
    store = StateStore()

    puw_connector = PuwConnector(config) if config.puw_enabled else None
    wps_connector = WpsConnector(config) if config.wps_enabled else None

    puw_job = _make_puw_job(puw_connector, calendar, store) if puw_connector else None
    wps_job = _make_wps_job(wps_connector, calendar, store) if wps_connector else None

    scheduler = build_scheduler(puw_job, wps_job, config)
    scheduler.start()

    log_daemon_started(
        puw_interval=config.puw_poll_interval_minutes if config.puw_enabled else None,
        wps_times=config.wps_poll_times if config.wps_enabled else None,
    )

    stop_event = [False]

    def _handle_shutdown(signum, frame):
        stop_event[0] = True

    signal.signal(signal.SIGTERM, _handle_shutdown)

    try:
        while not stop_event[0]:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        scheduler.shutdown(wait=True)
        log_daemon_stopped()


def main() -> None:
    parser = argparse.ArgumentParser(prog="ahe-sync")
    subparsers = parser.add_subparsers(dest="command")

    remove_parser = subparsers.add_parser("remove", help="Remove synced events from Google Calendar")
    remove_parser.add_argument(
        "--source",
        required=True,
        choices=["puw", "wps"],
        help="Which source to remove events for",
    )

    args = parser.parse_args()
    config = Config.load()

    if args.command == "remove":
        creds = get_valid_credentials(config)
        calendar = CalendarClient(creds, config.google_calendar_id)
        store = StateStore()
        _run_remove(args.source, calendar, store)
    else:
        _run_daemon(config)


if __name__ == "__main__":
    main()
