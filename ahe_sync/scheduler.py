"""APScheduler setup for the ahe-sync daemon.

PUW: IntervalTrigger(minutes=N) — configurable, minimum 10
WPS: CronTrigger(hour=H, minute=M, timezone="Europe/Warsaw") — twice daily
"""

from __future__ import annotations

from typing import Callable, TYPE_CHECKING

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

if TYPE_CHECKING:
    from .config import Config


def build_scheduler(
    puw_job: Callable | None,
    wps_job: Callable | None,
    config: "Config",
) -> BackgroundScheduler:
    """Build and return a configured BackgroundScheduler (not yet started).

    Jobs are only registered when the corresponding connector is enabled
    (credentials present in config).
    """
    scheduler = BackgroundScheduler()

    if puw_job is not None and config.puw_enabled:
        scheduler.add_job(
            puw_job,
            IntervalTrigger(minutes=config.puw_poll_interval_minutes),
            id="puw_sync",
            name="PUW sync",
            misfire_grace_time=60,
        )

    if wps_job is not None and config.wps_enabled:
        hours = ",".join(str(h) for h, _ in config.wps_poll_times)
        minutes = ",".join(str(m) for _, m in config.wps_poll_times)
        scheduler.add_job(
            wps_job,
            CronTrigger(hour=hours, minute=minutes, timezone="Europe/Warsaw"),
            id="wps_sync",
            name="WPS sync",
            misfire_grace_time=300,
        )

    return scheduler
