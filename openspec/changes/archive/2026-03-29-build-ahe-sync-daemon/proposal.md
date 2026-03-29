## Why

AHE (Akademia Humanistyczno-Ekonomiczna) eksternistyczne CS students must manually monitor two disconnected platforms — PUW (Moodle-based e-learning) and WPS (zjazd timetable) — with no unified view, no push notifications, and events posted with less than an hour's notice. The result is missed deadlines and manual calendar management. A local daemon that automatically syncs both platforms into Google Calendar eliminates this entirely.

## What Changes

- **New**: `ahe_sync/` Python package — the full daemon implementation
- **New**: `scripts/setup.py` — cross-platform setup script (creates venv, installs deps, copies `.env.example`)
- **New**: `pyproject.toml` + `requirements.txt` — package definition and pinned dependency lockfile
- **New**: `.env.example` — documented configuration template (safe to commit)
- **New**: PUW connector — authenticates via Moodle `wstoken`, fetches 3 months of calendar events, maps to `CalendarEvent`, syncs to Google Calendar every 10 minutes
- **New**: WPS connector — authenticates via JWT bearer, fetches zjazd timetable for current semester, syncs to Google Calendar at 12:00 and 21:00 CET
- **New**: Sync engine — pure `compute_diff()` logic; determines create/update/delete per event; per-event failure tracking with retry on next cycle
- **New**: Google OAuth flow — first-run browser consent with tiered storage prompt (`local` default / `memory` opt-in); token held in `~/.config/ahe-sync/` or process memory
- **New**: Google Calendar client — creates, updates, deletes events; all tool-managed events tagged via extended properties (`ahe-sync-source`, `ahe-sync-id`); never touches untagged events
- **New**: `ahe-sync remove --source puw|wps` subcommand — deletes all future tagged events for a given source; past events are never deleted
- **New**: Terminal logging — structured per-sync output with counts and actionable error messages

## Capabilities

### New Capabilities

- `setup`: One-command project setup via `python scripts/setup.py` — venv, deps, `.env` scaffold
- `puw-sync`: Authenticate with PUW/Moodle and sync calendar events (lectures, deadlines, exams) to Google Calendar on a 10-minute interval
- `wps-sync`: Authenticate with WPS and sync zjazd timetable entries to Google Calendar at 12:00 and 21:00 CET
- `google-auth`: Google OAuth 2.0 first-run consent with student-facing storage choice prompt; `local` stores `token.json`, `memory` keeps token in-process only
- `sync-engine`: Core diff logic — compare connector output against local state to produce create/update/delete operations; no I/O; fully unit-testable
- `event-tagging`: All tool-written Google Calendar events carry `ahe-sync-source` and `ahe-sync-id` extended properties; safe-delete guarantee
- `remove-command`: `ahe-sync remove --source puw|wps` cleanly removes future synced events without touching past events or personal calendar entries
- `daemon-scheduler`: APScheduler-based internal scheduler; PUW `IntervalTrigger(10min)`, WPS `CronTrigger(12:00+21:00, Europe/Warsaw)`; no OS cron dependency
- `observability`: Structured stdout logging per sync run with timestamps, counts, error class, and suggested student recovery action

### Modified Capabilities

*(none — this is the initial implementation)*

## Impact

- **New files**: entire `ahe_sync/` package, `scripts/`, `pyproject.toml`, `requirements.txt`, `.env.example`
- **External dependencies**: `apscheduler>=3.10`, `google-api-python-client>=2`, `google-auth-oauthlib>=1`, `python-dotenv>=1`, `requests>=2.31`
- **Runtime storage**: `~/.config/ahe-sync/state.json` (always), `~/.config/ahe-sync/token.json` (only if `TOKEN_STORAGE=local`), `~/.config/ahe-sync/prefs.json` (records first-run consent choice)
- **External systems touched**: PUW (`platforma.ahe.lodz.pl`), WPS (`wpsapi.ahe.lodz.pl`), Google Calendar API v3, Google OAuth 2.0
- **Security boundary**: student credentials never leave the student's machine; no data transmitted to the project team
- **OS support**: Windows, macOS, Linux (Python 3.10+ required)
