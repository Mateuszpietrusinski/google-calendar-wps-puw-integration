## Why

By default, events would sync into whatever calendar is hardcoded or defaulted — forcing students to manually move events or clutter their primary calendar. Users need to choose a specific Google Calendar (e.g., a dedicated "University" calendar) so synced events land exactly where they want them without polluting personal calendars.

## What Changes

- New `.env` variable `GOOGLE_CALENDAR_ID` to specify the target calendar by ID.
- On first run (when `GOOGLE_CALENDAR_ID` is absent), the daemon lists the user's available Google Calendars and prompts them to select one interactively.
- The selected calendar ID is persisted to `prefs.json` so the prompt is not repeated on subsequent starts.
- All event create/update/delete operations in `google/calendar.py` target the configured calendar instead of a hardcoded value.
- `google/auth.py` requests the `calendar.readonly` scope in addition to `calendar.events` to support listing calendars during selection.

## Capabilities

### New Capabilities
- `calendar-selection`: Interactive first-run calendar picker and `.env`-based override (`GOOGLE_CALENDAR_ID`) that determines which Google Calendar receives synced events.

### Modified Capabilities
- `google-auth`: OAuth scope must include `calendar.readonly` to allow listing the user's calendars during the selection step.

## Impact

- `ahe_sync/config.py` — new optional `GOOGLE_CALENDAR_ID` field.
- `ahe_sync/google/auth.py` — add `calendar.readonly` to OAuth scopes.
- `ahe_sync/google/calendar.py` — replace any hardcoded calendar reference with the configured ID; add `list_calendars()` helper used during selection.
- `ahe_sync/__main__.py` — invoke calendar-selection flow (after OAuth, before scheduler starts) when no calendar ID is configured.
- `.env.example` — document `GOOGLE_CALENDAR_ID` option.
- `prefs.json` schema — store `calendar_id` alongside `token_storage` choice.
