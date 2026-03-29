## 1. Project Scaffold

- [x] 1.1 Create `pyproject.toml` with project metadata, Python 3.10+ requirement, and dependencies (`apscheduler>=3.10`, `google-api-python-client>=2`, `google-auth-oauthlib>=1`, `python-dotenv>=1`, `requests>=2.31`)
- [x] 1.2 Create `requirements.txt` pinned lockfile via `pip freeze` after installing deps into a fresh venv
- [x] 1.3 Create `.env.example` documenting all keys: `PUW_USERNAME`, `PUW_PASSWORD`, `WPS_USERNAME`, `WPS_PASSWORD`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `TOKEN_STORAGE`, `GOOGLE_CALENDAR_ID`, `PUW_POLL_INTERVAL_MINUTES`, `WPS_POLL_TIMES_CET`, all reminder keys, `WPS_SEMESTER_FROM`, `WPS_SEMESTER_TO`
- [x] 1.4 Create `scripts/setup.py` — stdlib only: creates `.venv/`, runs `pip install -e .`, copies `.env.example → .env` if absent, validates Python ≥ 3.10, prints OS-specific start command
- [x] 1.5 Create `ahe_sync/` package skeleton: empty `__init__.py` files in `ahe_sync/`, `ahe_sync/google/`, `ahe_sync/connectors/`
- [x] 1.6 Update `.gitignore` to include `.venv/`, `.env`, `token.json`, `state.json`, `.state.tmp`, `prefs.json`, `__pycache__/`, `*.pyc`

## 2. Configuration

- [x] 2.1 Implement `ahe_sync/config.py`: load `.env` via `python-dotenv`, define `Config` dataclass with all fields and defaults, validate required fields on init, enforce `PUW_POLL_INTERVAL_MINUTES >= 10`, exit with missing-field list on failure
- [x] 2.2 Write unit tests for `config.py`: missing required fields, interval below minimum, valid config parses correctly

## 3. Core Models

- [x] 3.1 Implement `ahe_sync/models.py`: define `CalendarEvent`, `SyncPlan`, `SyncResult` dataclasses with all fields from architecture (`source`, `source_id`, `title`, `description`, `start`, `end`, `all_day`, `timemodified`, `checksum`)

## 4. State Store

- [x] 4.1 Implement `ahe_sync/state.py`: `StateStore` class with `load(source)`, `save(source, state)` methods; create `~/.config/ahe-sync/` directory on first use; atomic write via `os.replace()` on `.state.tmp`
- [x] 4.2 Write unit tests for `state.py`: load non-existent file returns empty dict, save + load round-trip, atomic write leaves file intact on simulated mid-write interruption

## 5. Sync Engine

- [x] 5.1 Implement `ahe_sync/sync_engine.py`: `compute_diff(fetched, state) → SyncPlan` — pure function, no I/O; correctly handles create/update/unchanged/delete cases
- [x] 5.2 Implement `apply_sync_plan(plan, calendar_client, state_store) → SyncResult` — per-event isolation: update state only for successes, log each failure, call `find_tagged_events` before create to prevent duplicates
- [x] 5.3 Write unit tests for `compute_diff`: all four cases (create, update, unchanged, delete), mixed batch, empty fetched list, empty state
- [x] 5.4 Write unit tests for duplicate prevention: `find_tagged_events` returns existing ID → create becomes update

## 6. Google OAuth

- [x] 6.1 Implement `ahe_sync/google/auth.py`: `get_valid_credentials(config) → Credentials`; load `prefs.json` to check stored choice; if `TOKEN_STORAGE` not set and no prefs, show consent prompt (default `[1] local`); run OAuth browser flow (auto-open browser, fallback to print URL + paste); store `token.json` (chmod 600) or hold in memory per choice; write `prefs.json`
- [x] 6.2 Implement silent token refresh: if access token expired and refresh token valid, refresh without re-prompting
- [x] 6.3 Write unit tests for `auth.py`: memory mode stores nothing to disk, local mode writes `token.json`, prompt default (Enter) selects local, `TOKEN_STORAGE` env var bypasses prompt

## 7. Google Calendar Client

- [x] 7.1 Implement `ahe_sync/google/calendar.py`: `CalendarClient` with `create_event(event) → gcal_id`, `update_event(gcal_id, event)`, `delete_event(gcal_id)`, `find_tagged_events(source, source_id) → str | None`; all create/update operations set `privateProperties` with `ahe-sync-source` and `ahe-sync-id`
- [x] 7.2 Write unit tests for `calendar.py` with mocked `google-api-python-client`: create sets extended properties, find_tagged_events uses correct query params, delete only accepts explicit gcal_id (no search by title)

## 8. PUW Connector

- [x] 8.1 Implement `ahe_sync/connectors/base.py`: `ConnectorBase` ABC with abstract `fetch() → list[CalendarEvent]`
- [x] 8.2 Implement `ahe_sync/connectors/puw.py`: `PuwConnector(ConnectorBase)` — `POST /login/token.php` auth, fetch 3 months via `core_calendar_get_calendar_monthly_view`, map events to `CalendarEvent` per event-type table (skip `attendance`, handle `timeduration=0`, all-day for `due`)
- [x] 8.3 Implement silent `wstoken` re-auth using `privatetoken` from initial auth response when `wstoken` is rejected
- [x] 8.4 Write unit tests for `puw.py` mapper with fixture JSON: `meeting_start` → timed event, `due` → all-day, `attendance` → skipped, `timeduration=0` → 0-duration, title construction `"{course.fullname} — {activityname}"`

## 9. WPS Connector

- [x] 9.1 Implement `ahe_sync/connectors/wps.py`: `WpsConnector(ConnectorBase)` — `POST /api/Profil/zaloguj` JWT auth, decode `StudentID` from JWT payload, fetch timetable via `GETPlanSzczegolowy`, map entries to `CalendarEvent`
- [x] 9.2 Implement proactive JWT refresh: check `exp - now < 5 minutes` before each API call; re-authenticate silently if true
- [x] 9.3 Implement semester date auto-detection: derive `DataOd`/`DataDo` from min/max `DataOD`/`DataDO` in API response; honour `.env` override
- [x] 9.4 Implement WPS checksum: `MD5(DataOD + DataDO + SalaNumer + SalaAdres + sorted_teachers)`
- [x] 9.5 Write unit tests for `wps.py` mapper with fixture JSON: on-site event has room details, webinar event has `"Online (Webinar)"`, title construction, checksum changes on field mutation

## 10. Scheduler

- [x] 10.1 Implement `ahe_sync/scheduler.py`: `build_scheduler(puw_job, wps_job, config) → BackgroundScheduler`; register PUW `IntervalTrigger` and WPS `CronTrigger(Europe/Warsaw)` only when respective connectors are enabled; parse `WPS_POLL_TIMES_CET` into cron hour/minute values

## 11. Entry Point and Daemon

- [x] 11.1 Implement `ahe_sync/__main__.py`: `main()` function — load config, call `get_valid_credentials`, build connectors and calendar client, build scheduler, register signal handlers (`SIGTERM`, `KeyboardInterrupt`), start scheduler, log startup line, block main thread; on signal: log shutdown line, stop scheduler, exit cleanly
- [x] 11.2 Implement `ahe_sync remove --source puw|wps` subcommand in `__main__.py`: call `find_tagged_events` for all future events of the given source, delete each, clear source from `state.json`, log deletion count, exit without starting scheduler

## 12. Observability

- [x] 12.1 Implement structured logging in `ahe_sync/observability.py` (or inline in `__main__`): format `[<timestamp> CET] [<SOURCE>] ✓/✗ ...`; ensure all error log lines include error class, message, and suggested recovery action
- [x] 12.2 Verify all error paths from specs have log coverage: auth failure (PUW + WPS + Google), network failure, Calendar API failure, missing `.env` fields

## 13. Integration and End-to-End

- [x] 13.1 Write integration test: full PUW sync cycle using fixture API responses and mocked `CalendarClient` — verify correct create/update/delete calls and state updates
- [x] 13.2 Write integration test: full WPS sync cycle using fixture API responses and mocked `CalendarClient` — verify checksum-based update detection
- [x] 13.3 Write integration test: `remove --source puw` — only future tagged PUW events deleted, past events and WPS events untouched, state cleared

## 14. Documentation

- [x] 14.1 Write `README.md` following *Docs for Developers* standard: prerequisites (Python 3.10+), clone, `python scripts/setup.py`, edit `.env`, start daemon, first-run OAuth prompt, stop daemon, `remove` command, reset instructions (`rm -rf ~/.config/ahe-sync/`), security warning for `token.json` and `.env`
- [x] 14.2 Add security note to README: never commit `.env` or `token.json`; file permission hardening command (`chmod 600`)
- [ ] 14.3 Validate README: one team member who was not the author completes setup from README alone in ≤ 30 minutes
