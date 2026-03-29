## ADDED Requirements

### Requirement: All tool-created events carry extended properties
Every Google Calendar event created by `ahe-sync` SHALL include two `privateProperties` extended properties: `ahe-sync-source` (value: `"puw"` or `"wps"`) and `ahe-sync-id` (value: the string representation of the source event ID).

#### Scenario: Created PUW event is tagged
- **WHEN** a PUW event is created in Google Calendar
- **THEN** the event's `privateProperties` contain `{"ahe-sync-source": "puw", "ahe-sync-id": "<moodle_event_id>"}`

#### Scenario: Created WPS event is tagged
- **WHEN** a WPS timetable entry is created in Google Calendar
- **THEN** the event's `privateProperties` contain `{"ahe-sync-source": "wps", "ahe-sync-id": "<IDPlanZajecPoz>"}`

---

### Requirement: Untagged events are never modified or deleted
The `CalendarClient` SHALL only update or delete events whose `gcal_event_id` was retrieved from `state.json`. It SHALL never perform a calendar-wide search by title, time range, or any other field.

#### Scenario: Personal event with same title is not touched
- **WHEN** the student has a personal Google Calendar event with the same title as a synced PUW event
- **THEN** the personal event is never updated or deleted by any sync operation

---

### Requirement: find_tagged_events queries by extended property
`find_tagged_events(source: str, source_id: str)` SHALL query Google Calendar using `privateExtendedProperty=ahe-sync-source=<source>` and `privateExtendedProperty=ahe-sync-id=<source_id>` filter parameters.

#### Scenario: Existing tagged event found for duplicate prevention
- **WHEN** `find_tagged_events("puw", "1001")` is called and an event with matching extended properties exists
- **THEN** the function returns that event's `gcal_event_id`

#### Scenario: No match returns None
- **WHEN** `find_tagged_events("puw", "9999")` is called and no matching tagged event exists
- **THEN** the function returns `None`
