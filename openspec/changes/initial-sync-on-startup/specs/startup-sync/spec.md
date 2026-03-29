## ADDED Requirements

### Requirement: Immediate sync runs on daemon startup for each enabled connector
When the daemon starts, it SHALL execute one full sync cycle for each enabled connector (PUW and/or WPS) before the scheduler begins. The startup sync SHALL use the same job function as scheduled syncs and SHALL log results using the standard sync result format.

#### Scenario: Both connectors sync on startup
- **WHEN** both `PUW_USERNAME`/`PUW_PASSWORD` and `WPS_USERNAME`/`WPS_PASSWORD` are set and the daemon starts
- **THEN** a PUW sync and a WPS sync each run to completion before the scheduler fires its first scheduled job

#### Scenario: Only PUW syncs on startup when WPS is disabled
- **WHEN** only PUW credentials are set and the daemon starts
- **THEN** a PUW startup sync runs; no WPS sync is attempted

#### Scenario: Only WPS syncs on startup when PUW is disabled
- **WHEN** only WPS credentials are set and the daemon starts
- **THEN** a WPS startup sync runs; no PUW sync is attempted

#### Scenario: Startup sync failure does not prevent scheduler from starting
- **WHEN** the PUW startup sync raises an error (e.g., auth failure, network timeout)
- **THEN** the error is logged with the standard error format, the WPS startup sync still runs, and the scheduler starts normally

#### Scenario: Startup sync results are logged
- **WHEN** the startup sync completes successfully
- **THEN** the log contains a line in the format: `[PUW] ✓ N created, N updated, N deleted`
