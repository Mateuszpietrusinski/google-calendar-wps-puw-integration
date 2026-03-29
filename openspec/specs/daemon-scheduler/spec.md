## ADDED Requirements

### Requirement: PUW sync runs on configurable interval with enforced minimum
The scheduler SHALL register a PUW sync job using `IntervalTrigger(minutes=N)` where `N` is `PUW_POLL_INTERVAL_MINUTES` from `.env` (default: 10). The daemon SHALL reject any value below 10 at startup with a clear error message.

#### Scenario: PUW job fires every 10 minutes by default
- **WHEN** `PUW_POLL_INTERVAL_MINUTES` is not set and the daemon starts
- **THEN** the PUW sync job is scheduled with a 10-minute interval

#### Scenario: Minimum interval enforced
- **WHEN** `PUW_POLL_INTERVAL_MINUTES=5` is set
- **THEN** the daemon exits at startup with: `Error: PUW_POLL_INTERVAL_MINUTES must be ≥ 10 (got 5)`

---

### Requirement: WPS sync runs at 12:00 and 21:00 CET
The scheduler SHALL register a WPS sync job using `CronTrigger(hour="12,21", minute=0, timezone="Europe/Warsaw")`. The scheduler SHALL handle CET/CEST transitions automatically.

#### Scenario: WPS job fires at 12:00 CET
- **WHEN** the system clock reaches 12:00 in the `Europe/Warsaw` timezone
- **THEN** the WPS sync job is triggered

#### Scenario: WPS times configurable via .env
- **WHEN** `WPS_POLL_TIMES_CET=08:00,20:00` is set
- **THEN** the WPS sync job fires at 08:00 and 20:00 `Europe/Warsaw` instead of the defaults

---

### Requirement: Daemon starts scheduler only — no CLI interaction after start
After setup and OAuth, `python -m ahe_sync` SHALL run a startup sync for each enabled connector, THEN start the APScheduler `BackgroundScheduler`, log a startup line, and block indefinitely on the main thread until a termination signal is received.

#### Scenario: Startup log line emitted after startup sync
- **WHEN** the daemon starts successfully
- **THEN** it runs startup syncs, then logs: `[DAEMON] Started. PUW: every N min | WPS: HH:MM, HH:MM CET`

#### Scenario: Startup sync error does not prevent daemon from starting
- **WHEN** a startup sync fails for one connector
- **THEN** the error is logged, the other connector's startup sync still runs, and the daemon starts normally

---

### Requirement: Graceful shutdown on SIGTERM / CTRL+C
The daemon SHALL catch `SIGTERM` and `KeyboardInterrupt`, shut down the scheduler cleanly (no partial sync state left inconsistent), and log a shutdown line before exiting.

#### Scenario: Clean shutdown on CTRL+C
- **WHEN** the student presses CTRL+C
- **THEN** the scheduler stops, any in-progress sync job completes or is cancelled cleanly, and the terminal shows: `[DAEMON] Stopped.`

#### Scenario: No partial state on shutdown
- **WHEN** the daemon is stopped mid-sync-cycle
- **THEN** `state.json` contains only entries for events that were fully and successfully applied before the shutdown signal
