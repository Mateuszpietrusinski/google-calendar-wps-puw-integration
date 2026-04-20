## Context

The daemon currently has no mechanism to target a specific Google Calendar — all events would be written to whatever calendar ID is hardcoded or defaulted. Students typically want a dedicated calendar (e.g., "Studia AHE") separate from personal events. This change introduces a calendar-selection step that runs once after OAuth and persists the user's choice so subsequent starts skip the prompt.

Affected modules: `config.py`, `google/auth.py`, `google/calendar.py`, `__main__.py`, `prefs.json` schema.

## Goals / Non-Goals

**Goals:**
- Allow `GOOGLE_CALENDAR_ID` in `.env` to specify the target calendar directly (no prompt).
- On first run without `GOOGLE_CALENDAR_ID`, list the user's calendars and prompt for selection; persist the choice in `prefs.json`.
- Ensure all calendar CRUD operations target the configured calendar.

**Non-Goals:**
- Creating or deleting Google Calendars.
- Syncing the same events into multiple calendars simultaneously.
- Allowing calendar change at runtime without restart.
- Migrating previously synced events when the target calendar changes.

## Decisions

### Decision 1: `GOOGLE_CALENDAR_ID` env var as primary override
Use the same `.env` pattern already established by `TOKEN_STORAGE`. Students who know their calendar ID skip the prompt entirely. Avoids adding a new config file format.

*Alternative considered*: A separate `--calendar` CLI flag. Rejected because the daemon is long-running and flags are awkward for a daemon; `.env` is already the canonical config mechanism here.

### Decision 2: Interactive prompt on first run, persisted to `prefs.json`
Follow the same pattern as the `TOKEN_STORAGE` consent prompt in `google-auth`. After OAuth completes, call `list_calendars()`, display a numbered list, and wait for input. Store `calendar_id` in `prefs.json` alongside `token_storage`.

*Alternative considered*: Always require `GOOGLE_CALENDAR_ID` in `.env` (fail hard if absent). Rejected because it breaks the zero-config first-run experience the PRD targets (≤ 30 min setup).

### Decision 3: Add `calendar.readonly` scope to OAuth
The Google Calendar API requires `https://www.googleapis.com/auth/calendar.readonly` to list a user's calendar list. Adding it alongside the existing `calendar.events` scope is minimal and avoids a separate credentials set.

*Risk*: Adding a new scope invalidates existing `token.json` files — users who already authorised will be prompted to re-consent once. This is acceptable; the scope change is transparent and happens at most once per install.

### Decision 4: Cap calendar list at 20, primary calendar first
`calendars.list` can return many entries (shared, read-only, holiday). Cap at 20, sort primary calendar first, then alphabetically by summary. If more exist, show a note directing users to set `GOOGLE_CALENDAR_ID` manually.

## Risks / Trade-offs

- **Scope re-consent** → Existing `token.json` will be rejected when new scope is detected. Mitigation: detect `InvalidGrantError` / scope mismatch on startup and trigger a fresh OAuth flow automatically with a clear message to the user.
- **User has no writable calendars** (e.g., only subscribed read-only calendars) → Mitigation: filter list to calendars where `accessRole` is `owner` or `writer`; if list is empty after filter, instruct user to create a calendar in Google Calendar first.
- **Non-interactive environment (cron/systemd without `GOOGLE_CALENDAR_ID`)** → Mitigation: if stdin is not a tty and no `GOOGLE_CALENDAR_ID` is set, daemon exits with a clear error message asking user to set the env var.

## Migration Plan

1. Deploy updated code.
2. Existing users without `GOOGLE_CALENDAR_ID`: on next daemon start, OAuth re-consent fires (new scope), then calendar-selection prompt runs once and persists to `prefs.json`.
3. Existing users with `GOOGLE_CALENDAR_ID` already set in `.env`: prompt is skipped; no re-consent if token already includes the new scope (first install after this change).
4. No rollback needed for `prefs.json` changes — old daemon ignores unknown keys.
