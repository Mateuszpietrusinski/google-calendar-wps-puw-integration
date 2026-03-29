## ADDED Requirements

### Requirement: PUW authentication via Moodle wstoken
The PUW connector SHALL authenticate by POSTing to `/login/token.php?username=&password=&service=moodle_mobile_app` and extracting `token` (`wstoken`) from the response. The connector SHALL re-authenticate silently using the stored `privatetoken` when `wstoken` is rejected (HTTP 401 or Moodle error code `invalidtoken`).

#### Scenario: Successful authentication
- **WHEN** valid PUW credentials are in `.env` and the connector authenticates
- **THEN** a `wstoken` is obtained and used as a query parameter on all subsequent Moodle API calls

#### Scenario: Invalid credentials
- **WHEN** PUW credentials are invalid
- **THEN** the sync cycle is aborted for this source, an error is logged with message: `AuthError: PUW login failed — check PUW_USERNAME / PUW_PASSWORD in .env`, and no calendar changes are made

---

### Requirement: Fetch three months of PUW calendar events
The PUW connector SHALL fetch the current month, next month, and the month after using `core_calendar_get_calendar_monthly_view`, for a total of 3 API calls per sync cycle.

#### Scenario: Three-month window fetched
- **WHEN** a PUW sync cycle runs
- **THEN** exactly 3 API calls are made — for the current, next, and following month

#### Scenario: PUW connector disabled when credentials absent
- **WHEN** `PUW_USERNAME` or `PUW_PASSWORD` is absent from `.env`
- **THEN** the PUW connector is not initialised and no PUW sync jobs are registered

---

### Requirement: PUW event type mapping to CalendarEvent
The PUW connector SHALL map Moodle event types to `CalendarEvent` according to the following rules:

| `eventtype` | `modulename` | Calendar treatment |
|---|---|---|
| `meeting_start` | `clickmeeting` | Timed: `timestart` → `timestart + timeduration` |
| `due` | `assign` | All-day on `timestart` date |
| `open` | `quiz` | Timed: exam window open |
| `close` | `quiz` | Timed: exam window close |
| `attendance` | — | **Skip** (not mapped in v1) |

Events with `timeduration = 0` SHALL be created as 0-duration Google Calendar events.

#### Scenario: Lecture event mapped as timed
- **WHEN** a `meeting_start` event with `timeduration > 0` is fetched from PUW
- **THEN** a `CalendarEvent` is created with `all_day=False`, `start=timestart`, `end=timestart+timeduration`

#### Scenario: Assignment deadline mapped as all-day
- **WHEN** a `due` event is fetched from PUW
- **THEN** a `CalendarEvent` is created with `all_day=True` on the date of `timestart`

#### Scenario: Attendance events skipped
- **WHEN** a Moodle event with `eventtype=attendance` is fetched
- **THEN** it is not included in the returned `list[CalendarEvent]` and no calendar event is created

#### Scenario: Zero-duration event
- **WHEN** a Moodle event has `timeduration=0`
- **THEN** a `CalendarEvent` is created with `start == end` (0-duration point event)

---

### Requirement: PUW event title and description
Each PUW `CalendarEvent` SHALL have title `"{course.fullname} — {activityname}"` and description containing `activitystr` and the direct `viewurl` link to the platform.

#### Scenario: Event title constructed correctly
- **WHEN** a Moodle event has `course.fullname="Bazy Danych"` and `activityname="Wykład 1"`
- **THEN** the `CalendarEvent.title` is `"Bazy Danych — Wykład 1"`

---

### Requirement: PUW change detection via timemodified
The PUW connector SHALL pass `timemodified` (epoch seconds) on each `CalendarEvent`. The sync engine SHALL detect an update when `fetched.timemodified != state[source_id].timemodified`.

#### Scenario: Rescheduled event detected as update
- **WHEN** a fetched event has a `timemodified` value greater than the value stored in `state.json`
- **THEN** `compute_diff` includes that event in `SyncPlan.to_update`

---

### Requirement: PUW deletion detection
An event previously synced (present in `state.json`) but absent from the current 3-month API response SHALL be included in `SyncPlan.to_delete`.

#### Scenario: Cancelled event deleted from calendar
- **WHEN** an event ID is in `state.json` but not returned by the 3-month Moodle API fetch
- **THEN** the corresponding Google Calendar event is deleted
