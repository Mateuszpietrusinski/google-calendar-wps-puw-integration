## ADDED Requirements

### Requirement: remove command deletes future tagged events by source
`python -m ahe_sync remove --source puw` and `python -m ahe_sync remove --source wps` SHALL delete all **future** Google Calendar events tagged with `ahe-sync-source=<source>`. Past events (end time before the current moment) SHALL never be deleted.

#### Scenario: Future PUW events deleted
- **WHEN** `python -m ahe_sync remove --source puw` is run
- **THEN** all Google Calendar events with `ahe-sync-source=puw` and `end > now()` are deleted

#### Scenario: Past PUW events retained
- **WHEN** `python -m ahe_sync remove --source puw` is run
- **THEN** Google Calendar events with `ahe-sync-source=puw` and `end <= now()` are not deleted and remain in the calendar permanently

#### Scenario: WPS events unaffected by PUW remove
- **WHEN** `python -m ahe_sync remove --source puw` is run
- **THEN** no events tagged `ahe-sync-source=wps` are deleted

---

### Requirement: remove command clears corresponding state
After deleting events, `remove --source <source>` SHALL remove all entries for that source from `state.json`.

#### Scenario: State cleared after remove
- **WHEN** `python -m ahe_sync remove --source wps` completes
- **THEN** `state.json` contains no entries under the `wps` key

---

### Requirement: remove command does not start the scheduler
`python -m ahe_sync remove` SHALL perform the deletion and exit. It SHALL NOT start the daemon scheduler.

#### Scenario: Remove exits after completion
- **WHEN** `python -m ahe_sync remove --source puw` is run
- **THEN** the process exits after logging the count of deleted events; no scheduler is started

---

### Requirement: remove command reports deletion count
After completing, the remove command SHALL log the number of events deleted.

#### Scenario: Deletion count logged
- **WHEN** `remove --source puw` deletes 7 events
- **THEN** the terminal output includes: `[REMOVE] [PUW] 7 future events deleted`
