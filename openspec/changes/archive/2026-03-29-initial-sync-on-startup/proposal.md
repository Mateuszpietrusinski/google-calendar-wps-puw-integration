## Why

When the daemon starts, the first scheduled sync doesn't fire until the configured interval elapses (up to 10 minutes for PUW, up to 9 hours for WPS). Users launching the daemon for the first time — or after a restart — see no calendar updates until that delay passes, which is confusing and error-prone.

## What Changes

- On daemon startup, run a full sync immediately for each enabled connector (PUW and/or WPS) before handing control to the scheduler.
- Startup sync errors are handled with the same per-source isolation as scheduled syncs: one connector failing does not block the other or prevent the scheduler from starting.
- Log output distinguishes the startup sync from subsequent scheduled syncs.

## Capabilities

### New Capabilities

- `startup-sync`: Immediate sync execution at daemon startup before the scheduler's first scheduled fire

### Modified Capabilities

- `daemon-scheduler`: Startup sequence changes — initial sync now runs before `scheduler.start()`

## Impact

- `ahe_sync/__main__.py` — add startup sync invocation in `_run_daemon()` before `scheduler.start()`
- `ahe_sync/observability.py` — add `log_startup_sync_result()` or reuse `log_sync_result()` with a startup context label
- No new dependencies, no API changes, no breaking changes
