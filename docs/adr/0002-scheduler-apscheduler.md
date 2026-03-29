# ADR-0002: Use APScheduler 3.x for Daemon Scheduling

**Date:** 2026-03-29
**Status:** Proposed
**Deciders:** Architect, Team
**Related ADRs:** —

---

## Context

The PRD (§4.1, §4.3) requires an **internal scheduler** — no OS-level cron or Task Scheduler. The scheduler must:
- Run PUW sync every 10 minutes (interval-based, minimum enforced in code)
- Run WPS sync at exactly 12:00 CET and 21:00 CET using `Europe/Warsaw` timezone
- Not drift over time (wall-clock accuracy, not sleep-loop)
- Be restart-stable (next scheduled time recalculated from current time on start; no missed-run backfill)
- Work on Windows, macOS, and Linux

Three options were considered:
1. `APScheduler 3.x` — mature in-process scheduler, `IntervalTrigger` + `CronTrigger`, timezone support
2. `schedule` library — simple API but no native timezone support; requires manual wrapping
3. Custom `threading.Timer` loop — maximum control but no timezone awareness; drift risk

## Decision

We will use **APScheduler 3.x** with a `BackgroundScheduler`.

PUW job: `IntervalTrigger(minutes=10)` with `min_interval` enforcement in `config.py`.
WPS job: `CronTrigger(hour="12,21", minute=0, timezone="Europe/Warsaw")`.

```python
# scheduler.py sketch
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

def build_scheduler(puw_job, wps_job, config) -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    if config.puw_enabled:
        scheduler.add_job(puw_job, IntervalTrigger(minutes=config.puw_poll_interval_minutes))
    if config.wps_enabled:
        scheduler.add_job(wps_job, CronTrigger(hour="12,21", minute=0, timezone="Europe/Warsaw"))
    return scheduler
```

## Consequences

### Positive
- `CronTrigger` with `timezone="Europe/Warsaw"` handles CET/CEST transitions automatically — no manual DST handling.
- `IntervalTrigger` fires relative to start time; no drift accumulation.
- APScheduler 3.x is stable, well-documented, and dependency-free for the `BackgroundScheduler` use case.
- Missed runs on restart are **not backfilled** (default `misfire_grace_time` behaviour), which is correct for this use case — a missed sync just waits for the next interval.

### Negative / Trade-offs
- APScheduler 3.x is in maintenance mode; APScheduler 4.x has an async-first API. For a synchronous daemon this is not a problem, but forks targeting async should evaluate APScheduler 4.x.
- Adds one dependency (~400 KB installed).

### Neutral / Notes
- The 10-minute minimum for PUW polling is enforced in `config.py` validation, not in the scheduler itself. If a student sets `PUW_POLL_INTERVAL_MINUTES=5`, startup exits with: `PUW_POLL_INTERVAL_MINUTES must be ≥ 10 (got 5)`.
