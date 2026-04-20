## 1. Config & Environment

- [x] 1.1 Add optional `GOOGLE_CALENDAR_ID` field to `Config` dataclass in `config.py`; no hard-exit if absent
- [x] 1.2 Add `calendar_id` key to `prefs.json` read/write logic in `state.py` (or wherever `prefs.json` is managed)
- [x] 1.3 Update `.env.example` with `GOOGLE_CALENDAR_ID` and a comment explaining how to find a calendar ID

## 2. OAuth Scope Update

- [x] 2.1 Add `https://www.googleapis.com/auth/calendar.readonly` to the OAuth scopes list in `google/auth.py`
- [x] 2.2 Add scope-mismatch detection on startup: if `token.json` scopes don't include `calendar.readonly`, delete the token and trigger a fresh OAuth flow with a clear message

## 3. Calendar Listing Helper

- [x] 3.1 Implement `list_calendars(credentials) -> list[dict]` in `google/calendar.py` that calls `calendarList.list`, filters to `accessRole` in `{owner, writer}`, caps at 20, and sorts primary first then alphabetically
- [x] 3.2 Add unit test for `list_calendars` filtering and sorting logic using a mocked API response

## 4. Interactive Calendar Selection

- [x] 4.1 Implement `select_calendar(credentials, prefs_path) -> str` in `google/calendar.py` (or a new `google/calendar_select.py`): detect non-tty and exit with error, display numbered list, read input, persist `calendar_id` to `prefs.json`, return selected ID
- [x] 4.2 Handle "invalid calendar ID from env var" case: after OAuth, verify `GOOGLE_CALENDAR_ID` exists in the user's calendar list; exit with error message if not found
- [x] 4.3 Add unit tests for selection flow: valid input, out-of-range input, non-tty exit, >20 calendars truncation message, no writable calendars exit

## 5. Wire Into Startup

- [x] 5.1 In `__main__.py`, after OAuth completes, resolve the target calendar ID: check env var → check `prefs.json` → run interactive selection; store resolved ID in `Config` or pass to calendar module
- [x] 5.2 Update all `google/calendar.py` CRUD calls (`create_event`, `update_event`, `delete_event`, `find_tagged_events`) to use the resolved `calendar_id` instead of any hardcoded value

## 6. Validation & Documentation

- [ ] 6.1 Manual end-to-end test: fresh install, no `GOOGLE_CALENDAR_ID`, verify prompt appears, selection is persisted, and second start skips prompt
- [ ] 6.2 Manual test: set `GOOGLE_CALENDAR_ID` in `.env`, verify prompt is skipped and events land in the correct calendar
- [x] 6.3 Update `docs/architecture/README.md` to document the calendar-selection startup step and `prefs.json` schema change
