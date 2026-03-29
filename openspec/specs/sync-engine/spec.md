## ADDED Requirements

### Requirement: compute_diff produces correct SyncPlan
`compute_diff(fetched: list[CalendarEvent], state: dict) → SyncPlan` SHALL be a pure function with no I/O. It SHALL compare fetched events against stored state to produce three disjoint lists: events to create, events to update (with their existing `gcal_event_id`), and `gcal_event_id`s to delete.

#### Scenario: New event added to create list
- **WHEN** a fetched event's `source_id` is absent from `state`
- **THEN** the event appears in `SyncPlan.to_create`

#### Scenario: Changed event added to update list
- **WHEN** a fetched event's `source_id` is in `state` and its change-detection value (timemodified or checksum) differs
- **THEN** the event and its existing `gcal_event_id` appear in `SyncPlan.to_update`

#### Scenario: Unchanged event excluded from plan
- **WHEN** a fetched event's `source_id` is in `state` and its change-detection value is identical
- **THEN** the event does not appear in any list in the `SyncPlan`

#### Scenario: Missing event added to delete list
- **WHEN** a `source_id` exists in `state` but is absent from the fetched list
- **THEN** its `gcal_event_id` appears in `SyncPlan.to_delete`

---

### Requirement: Per-event failure isolation during apply
`apply_sync_plan` SHALL process each calendar operation independently. A failure on one event SHALL NOT prevent processing of remaining events. State SHALL be updated only for successfully applied operations.

#### Scenario: Partial failure leaves successful events in state
- **WHEN** 5 events are in `SyncPlan.to_create` and 2 Google Calendar API calls fail
- **THEN** state is updated for the 3 successes, the 2 failures are not recorded in state, and the next sync cycle retries them

#### Scenario: Errors logged per failed event
- **WHEN** a Calendar API call fails for a specific event
- **THEN** an error log line is emitted with the source, event title, error class, and suggested recovery action

---

### Requirement: Duplicate prevention on retry
Before executing a create operation, `apply_sync_plan` SHALL call `find_tagged_events(source_id)` to check for an existing tagged Google Calendar event. If found, the create SHALL be converted to an update.

#### Scenario: Duplicate create avoided after previous partial failure
- **WHEN** an event was created in Google Calendar on a previous cycle but not recorded in state (due to a failure), and the next sync cycle attempts to create it again
- **THEN** `find_tagged_events` returns the existing event ID and the operation becomes an update instead of a create, producing no duplicate

---

### Requirement: State written atomically
After each `apply_sync_plan` call, the updated state SHALL be written to `.state.tmp` and then atomically renamed to `state.json` using `os.replace()`.

#### Scenario: State file is not corrupted on crash during write
- **WHEN** the process crashes mid-write to `state.json`
- **THEN** the previous `state.json` remains intact (the `.tmp` file is incomplete but the rename was not executed)
