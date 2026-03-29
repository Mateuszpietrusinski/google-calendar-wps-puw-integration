## Context

AHE students currently check PUW and WPS manually. The daemon runs locally on the student's machine with no server-side component — the student's credentials never leave their machine. Both PUW and WPS expose stable REST APIs (confirmed in PRD §6), so no scraping is required. The Google Calendar API v3 is used for all calendar writes.

Full architecture diagrams and ADRs: `docs/architecture/README.md`, `docs/adr/`.

## Goals / Non-Goals

**Goals:**
- Implement the full `ahe_sync/` package as specified in `docs/architecture/README.md §5`
- PUW sync every 10 minutes; WPS sync at 12:00 + 21:00 CET (`Europe/Warsaw`)
- Google OAuth with tiered token storage — `local` (default, consent prompt) or `memory` (opt-in)
- Zero personal event deletion — only events tagged `ahe-sync-source` are ever touched
- Per-event failure isolation — partial sync failures retry on next cycle without corrupting state
- Cross-platform: Windows, macOS, Linux with Python 3.10+
- Setup time ≤ 30 minutes from clone to running daemon

**Non-Goals:**
- No graphical UI
- No PyPI publishing (security: no public artifact risk — see ADR-0001)
- No OS-level cron or Task Scheduler
- No multi-user or SaaS deployment
- No WPS exam schedule (deferred post-MVP)
- No retry queue within a single cycle

## Decisions

### D1 — Flat module structure (ADR-0004)
**Decision:** `ahe_sync/` uses a flat layout with `connectors/` and `google/` subpackages. No full hexagonal architecture.

**Why:** Two connectors, one output. Full hexagonal (ports/adapters/domain) would add ~6 boilerplate files for two concrete adapters that will never be swapped. The key testability guarantee of hexagonal — sync engine with no I/O — is preserved by convention: `sync_engine.py` imports only from `models.py`.

**Alternative considered:** Full hexagonal with `ports/outbound/CalendarPort.py`. Rejected — over-engineered for this scope.

---

### D2 — Clone-and-run packaging (ADR-0001)
**Decision:** `python scripts/setup.py` is the only installation method. No PyPI package.

**Why:** Publishing to PyPI creates a permanent public artifact. Any accidental inclusion of a token file or `.env` in a future build would expose student credentials publicly and irreversibly. Clone-and-run eliminates that attack surface entirely.

**Alternative considered:** `pipx install ahe-sync` from PyPI. Rejected — security risk outweighs convenience for a student-credentials tool.

---

### D3 — APScheduler 3.x (ADR-0002)
**Decision:** `BackgroundScheduler` with `IntervalTrigger(minutes=10)` for PUW and `CronTrigger(hour="12,21", minute=0, timezone="Europe/Warsaw")` for WPS.

**Why:** Handles CET/CEST transitions automatically. No drift. No OS dependency. Missed runs on restart are not backfilled — correct behaviour for this use case.

**Alternative considered:** `schedule` library (no native timezone support), custom `threading.Timer` (drift risk). Both rejected.

---

### D4 — Tiered token storage with consent prompt (ADR-0003)
**Decision:** First-run interactive prompt offers `[1] local` (default, `~/.config/ahe-sync/token.json`, chmod 600) or `[2] memory` (opt-in, in-process only). Choice stored in `prefs.json`. Overridable via `TOKEN_STORAGE` in `.env`.

**Why:** Defaulting to `local` matches the expected UX for a daemon on a personal laptop (no re-auth on restart). The consent prompt ensures students are informed before any credential hits disk. `memory` mode is available for shared machines and privacy-conscious users.

**In-memory restart behaviour:** Daemon auto-opens browser for OAuth; falls back to printing URL if browser unavailable (headless/SSH).

**Alternative considered:** Unconditional `token.json` storage (original ADR-0003 v1). Rejected — no student consent, RODO concern.

---

### D5 — `sync_engine.py` as pure functions
**Decision:** `compute_diff(fetched: list[CalendarEvent], state: dict) → SyncPlan` and `apply_sync_plan(plan: SyncPlan, calendar: CalendarClient, state: StateStore) → SyncResult` are the two public functions. `compute_diff` has zero I/O and is fully unit-testable with fixture data.

**Why:** The core create/update/delete logic is the highest-risk area for bugs (especially safe deletion). Pure functions are trivially testable without mocks.

---

### D6 — State as JSON file
**Decision:** `~/.config/ahe-sync/state.json` — written atomically via `os.replace()` after a `.state.tmp` write.

**Why:** The sync volume (tens to low hundreds of events) does not warrant a database. JSON is human-inspectable and trivially resettable (`rm state.json` restores clean slate). Atomic write prevents corruption on mid-write crash.

**Schema:**
```json
{
  "puw": { "<source_id>": { "gcal_event_id": "...", "timemodified": 1712345678 } },
  "wps": { "<source_id>": { "gcal_event_id": "...", "checksum": "abc123" } }
}
```

---

### D7 — Per-event failure isolation
**Decision:** If `N` events are being synced and `K` Calendar API writes fail, state is updated only for the `N-K` successes. The `K` failures are retried on the next cycle.

**Why:** Avoids marking an event as synced when it wasn't, which would cause it to be silently skipped forever.

**Duplicate prevention on retry:** Before creating an event, `find_tagged_events(source_id)` checks for an existing tagged event. If found, the create becomes an update.

---

### D8 — WPS change detection via field checksum
**Decision:** WPS events have no `timemodified` field. Change detection uses `MD5(DataOD + DataDO + SalaNumer + SalaAdres + Dydaktyk[0].ImieNazwisko)`.

**Why:** `IDPlanZajecPoz` is stable — it does not change when a class is rescheduled. The checksum catches room changes, time changes, and teacher changes.

---

### D9 — WPS semester date auto-detection
**Decision:** On each WPS sync cycle, call `GETPlanSzczegolowy` without `DataOd`/`DataDo` bounds first to get the full available range, then use the min/max `DataOD`/`DataDO` from the response as the semester bounds for subsequent calls. Student can override via `WPS_SEMESTER_FROM` / `WPS_SEMESTER_TO` in `.env`.

**Why:** Hardcoding semester dates requires a code update each semester. The API response itself contains the authoritative range.

---

### D10 — WPS JWT proactive refresh
**Decision:** Before each WPS API call, check `exp - now < 5 minutes`. If true, re-authenticate silently using stored WPS credentials from config.

**Why:** JWT lifetime is ~6 hours (`expires_in: 21599`). A mid-run expiry would cause a partial sync failure. Proactive refresh avoids this without adding retry complexity.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Personal event accidentally deleted | `delete_event()` only accepts IDs from `state.json`; `find_tagged_events()` filters by extended property. Automated tests required for all delete paths (PRD §9). |
| Moodle API rate-limits at 3 calls / 10 min | Test against live instance before build sprint. If rate-limited, stagger requests with 2s delay between monthly fetches. |
| Google OAuth "unverified app" warning deters students | Document warning in README. Investigate shared-app verification feasibility (PRD §7 open item — Architect deadline end of March 2026). |
| Shared OAuth Client Secret exposure | Client Secret distributed out-of-band (never committed). Students using Path B supply their own via `.env`. |
| `state.json` corruption on crash during write | Atomic write via `os.replace()` ensures only complete files are committed. |
| Student machine off — sync missed | Document clearly in README. No in-scope fix for v1. |
| WPS semester boundary unknown at runtime | D9 auto-detection handles this; `.env` override available as fallback. |

## Migration Plan

Initial release — no migration needed. This is a greenfield implementation.

**First-time student setup:**
1. `git clone` → `python scripts/setup.py` → edit `.env` → `python -m ahe_sync`
2. First-run OAuth consent prompt (token storage choice)
3. Daemon starts, initial sync runs immediately, then on schedule

**Reset / uninstall:**
- `python -m ahe_sync remove --source puw` and/or `--source wps` to clear future events
- Stop the daemon process
- `rm -rf ~/.config/ahe-sync/` to remove all local state and tokens
- Delete the cloned repository

## Open Questions

- **Google OAuth shared app verification** — team deadline end of March 2026. If unverified warning is a hard block, all students must use Path B (own Client ID/Secret). README must cover both paths.
- **`attendance` eventtype (PUW)** — skipped in v1 per architecture decision. Confirm with PM this is acceptable for MVP.
- **`timeduration: 0` events (PUW)** — rendered as 0-duration Google Calendar events. Confirm with PM this is the preferred UX vs. a 1-hour default.
- **Moodle `wstoken` expiry** — `privatetoken` in auth response can regenerate `wstoken`. Implement silent re-auth using `privatetoken` before falling back to re-prompting student for credentials.
