## ADDED Requirements

### Requirement: GOOGLE_CALENDAR_ID env var sets target calendar without prompt
If `GOOGLE_CALENDAR_ID` is set in `.env`, the daemon SHALL use that calendar ID as the sync target and SHALL NOT display the calendar-selection prompt.

#### Scenario: Env var present — prompt skipped
- **WHEN** `GOOGLE_CALENDAR_ID` is set in `.env`
- **THEN** the daemon uses that calendar ID for all event operations and does not list or prompt for calendars

#### Scenario: Env var present with invalid calendar ID
- **WHEN** `GOOGLE_CALENDAR_ID` is set but the calendar does not exist or is not accessible by the authenticated account
- **THEN** the daemon exits with an error message: `GOOGLE_CALENDAR_ID '<id>' not found or not accessible. Check your .env.`

---

### Requirement: Interactive calendar selection on first run
When `GOOGLE_CALENDAR_ID` is absent and no calendar has been previously selected (no `calendar_id` in `prefs.json`), the daemon SHALL list the user's writable Google Calendars and prompt for selection after the OAuth flow completes.

#### Scenario: User selects a calendar from the list
- **WHEN** the user enters a valid number from the displayed list
- **THEN** the daemon saves that calendar's ID to `prefs.json` as `calendar_id` and proceeds to the scheduler

#### Scenario: Only writable calendars shown
- **WHEN** the calendar list is fetched
- **THEN** only calendars where `accessRole` is `owner` or `writer` are shown; read-only and holiday calendars are excluded

#### Scenario: Primary calendar listed first
- **WHEN** the calendar list is displayed
- **THEN** the primary calendar (where `primary: true`) is shown first, followed by remaining calendars sorted alphabetically by summary

#### Scenario: More than 20 calendars available
- **WHEN** the user has more than 20 writable calendars
- **THEN** the daemon displays the first 20 and appends: `More calendars available. Set GOOGLE_CALENDAR_ID in .env to use one not listed.`

#### Scenario: No writable calendars found
- **WHEN** the authenticated account has no calendars with `accessRole` of `owner` or `writer`
- **THEN** the daemon exits with: `No writable Google Calendars found. Create a calendar at calendar.google.com and restart.`

---

### Requirement: Selection persisted to prefs.json
The selected calendar ID SHALL be written to `~/.config/ahe-sync/prefs.json` under the key `calendar_id` so the prompt is not repeated on subsequent starts.

#### Scenario: Subsequent starts skip the prompt
- **WHEN** `prefs.json` contains a `calendar_id` entry and `GOOGLE_CALENDAR_ID` is not set in `.env`
- **THEN** the daemon uses the persisted `calendar_id` without displaying the calendar-selection prompt

#### Scenario: prefs.json calendar_id overridden by env var
- **WHEN** both `prefs.json` contains `calendar_id` and `GOOGLE_CALENDAR_ID` is set in `.env`
- **THEN** the env var value takes precedence

---

### Requirement: Non-interactive environment handling
When the daemon detects it is not running in an interactive terminal (stdin is not a tty) and no calendar ID is configured, it SHALL exit with a clear error rather than hanging waiting for input.

#### Scenario: Non-tty without GOOGLE_CALENDAR_ID and no persisted choice
- **WHEN** stdin is not a tty and `GOOGLE_CALENDAR_ID` is absent from `.env` and `prefs.json` has no `calendar_id`
- **THEN** the daemon exits with: `Calendar selection requires an interactive terminal. Set GOOGLE_CALENDAR_ID in .env and restart.`
