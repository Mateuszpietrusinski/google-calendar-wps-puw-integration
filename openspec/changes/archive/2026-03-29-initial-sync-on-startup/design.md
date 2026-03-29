## Context

Currently `_run_daemon()` in `__main__.py` builds connectors, builds the scheduler, calls `scheduler.start()`, then blocks. The first PUW sync fires after up to 10 minutes; the first WPS sync fires at the next 12:00 or 21:00 CET — potentially 9+ hours away. A student who just ran `python -m ahe_sync` for the first time sees nothing happen in their calendar and has no feedback that the daemon is working correctly.

The fix is small and isolated to `_run_daemon()`: call the sync jobs once synchronously before handing control to the scheduler.

## Goals / Non-Goals

**Goals:**
- Calendar is populated immediately on every daemon start (first-run and restart)
- Startup sync uses the exact same job functions as scheduled syncs — no duplicated logic
- A single connector failure does not block the other connector or the scheduler from starting
- Log output makes it clear which syncs are startup vs scheduled

**Non-Goals:**
- Changing the scheduler interval or cron expressions
- Backfilling missed syncs that occurred while the daemon was stopped
- Adding a `--no-startup-sync` flag (YAGNI for now)

## Decisions

**D1 — Call existing job functions directly, not the connectors**

`_make_puw_job()` and `_make_wps_job()` already return closures that fetch, diff, apply, and log. Calling `puw_job()` / `wps_job()` in the startup sequence reuses all of that error handling and logging. The alternative (calling `connector.fetch()` directly) would duplicate error handling logic.

**D2 — Run startup syncs sequentially before `scheduler.start()`**

Sequential execution keeps the startup path simple and avoids race conditions with the scheduler's first fire. The delay from running PUW then WPS back-to-back is negligible (seconds). Parallel execution would add complexity for no real benefit.

**D3 — Reuse `log_sync_result()` — no new log function needed**

The existing log format `[SOURCE] ✓ N created, N updated, N deleted` is sufficient. The startup context is implied by timing (the daemon just started). Adding a separate `[STARTUP]` label would add noise without value.

## Risks / Trade-offs

- **[Risk] Startup delay if an API is slow** → Mitigated: both connectors have 30-second timeouts, and errors are caught per-connector, so the worst case is 60 seconds before the scheduler starts. Acceptable for a local daemon.
- **[Risk] Duplicate events if daemon is restarted quickly** → Not a risk: `apply_sync_plan` already deduplicates via `find_tagged_events` and checksum comparison — restarts are idempotent.

## Migration Plan

No migration needed. Change is additive — existing users just get an immediate sync on next restart. No state format changes, no `.env` changes.
