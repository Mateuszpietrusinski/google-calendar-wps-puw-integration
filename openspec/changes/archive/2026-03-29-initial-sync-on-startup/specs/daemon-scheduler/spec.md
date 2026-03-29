## MODIFIED Requirements

### Requirement: Daemon starts scheduler only — no CLI interaction after start
After setup and OAuth, `python -m ahe_sync` SHALL run a startup sync for each enabled connector, THEN start the APScheduler `BackgroundScheduler`, log a startup line, and block indefinitely on the main thread until a termination signal is received.

#### Scenario: Startup log line emitted after startup sync
- **WHEN** the daemon starts successfully
- **THEN** it runs startup syncs, then logs: `[DAEMON] Started. PUW: every N min | WPS: HH:MM, HH:MM CET`

#### Scenario: Startup sync error does not prevent daemon from starting
- **WHEN** a startup sync fails for one connector
- **THEN** the error is logged, the other connector's startup sync still runs, and the daemon starts normally
