## 1. Startup Sync in Daemon Entry Point

- [x] 1.1 In `ahe_sync/__main__.py`, add a `_run_startup_syncs(puw_job, wps_job)` helper that calls `puw_job()` if not None, then `wps_job()` if not None
- [x] 1.2 Call `_run_startup_syncs(puw_job, wps_job)` in `_run_daemon()` after building jobs and before `scheduler.start()`

## 2. Tests

- [x] 2.1 Write unit test: both jobs called on startup when both connectors are enabled
- [x] 2.2 Write unit test: only PUW job called when WPS is disabled (wps_job is None)
- [x] 2.3 Write unit test: only WPS job called when PUW is disabled (puw_job is None)
- [x] 2.4 Write unit test: PUW startup failure does not prevent WPS job from running and does not raise
