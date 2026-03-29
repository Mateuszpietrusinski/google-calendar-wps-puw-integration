## ADDED Requirements

### Requirement: Structured sync result log line per cycle
After each sync cycle, the daemon SHALL log a single summary line to stdout with: timestamp (ISO with timezone), source (`PUW` or `WPS`), and counts of events created, updated, and deleted.

#### Scenario: Successful PUW sync logged
- **WHEN** a PUW sync cycle completes with 2 created, 0 updated, 1 deleted
- **THEN** stdout shows: `[2026-04-01 12:00:01 CET] [PUW] ✓ 2 created, 0 updated, 1 deleted`

#### Scenario: Clean run with no changes logged
- **WHEN** a sync cycle completes with no changes
- **THEN** stdout shows: `[2026-04-01 12:00:01 CET] [PUW] ✓ 0 created, 0 updated, 0 deleted`

---

### Requirement: Error log includes actionable recovery message
When a sync cycle encounters an error, the daemon SHALL log: timestamp, source, error class, human-readable message, and a suggested recovery action the student can take.

#### Scenario: Auth error logged with recovery action
- **WHEN** PUW authentication fails
- **THEN** stdout shows: `[2026-04-01 12:00:02 CET] [PUW] ✗ AuthError: PUW login failed — check PUW_USERNAME / PUW_PASSWORD in .env`

#### Scenario: Network error logged with recovery action
- **WHEN** the WPS API is unreachable
- **THEN** stdout shows a line containing `NetworkError` and the message `WPS unreachable — sync skipped, will retry at next scheduled time`

---

### Requirement: Startup and shutdown lines logged
The daemon SHALL emit a startup log line when the scheduler begins and a shutdown log line when it stops.

#### Scenario: Startup line format
- **WHEN** the daemon starts successfully
- **THEN** stdout shows: `[<timestamp> CET] [DAEMON] Started. PUW: every N min | WPS: HH:MM, HH:MM CET`

#### Scenario: Shutdown line format
- **WHEN** the daemon stops cleanly
- **THEN** stdout shows: `[<timestamp> CET] [DAEMON] Stopped.`

---

### Requirement: .env validation failure exits with field list
If required `.env` fields are missing at startup, the daemon SHALL exit immediately and print the names of all missing fields before any other initialisation occurs.

#### Scenario: Missing credentials at startup
- **WHEN** `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are absent from `.env`
- **THEN** the daemon exits with: `Error: Missing required .env fields: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET`
