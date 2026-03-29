# PRD: AHE Calendar Integration

## Document Info
| Field   | Value                              |
|---------|------------------------------------|
| Version | v1.2                               |
| Date    | 2026-03-16                         |
| Author  | PM (AI-assisted)                   |
| License | MIT                                |
| Status  | Draft — ready for Architect review |

---

## 1. Problem Statement

Students at Akademia Humanistyczno-Ekonomiczna (AHE) must manually monitor two disconnected platforms — the e-learning platform (**PUW**, platforma.ahe.lodz.pl) and the academic schedule system (**WPS**) — to stay on top of lectures, deadlines, and exams. These are two separate systems serving different data needs:

- **PUW** publishes events, tasks, and deadlines irregularly — sometimes with less than an hour's notice.
- **WPS** publishes the zjazd timetable (plan zajęć), which changes infrequently but is the single source of truth for when and where classes take place.

There is no unified view, and the cognitive overhead of juggling both systems leads to missed deadlines and poor time management.

The goal is a lightweight, **MIT-licensed open-source connector** built in **Node.js / TypeScript** that runs locally on a student's machine and automatically syncs events from both PUW and WPS into their personal Google Calendar — with no data transmitted to the project team or any third party other than Google.

---

## 2. Goals & Success Metrics

| Goal | Metric | Target |
|------|--------|--------|
| Students stop missing new PUW events | Time between event publication and calendar sync | ≤ 10 minutes (minimum poll interval enforced at 10 min) |
| Reduce manual calendar entry | Events auto-added without user action after initial setup | TBC — confirmed once ICS schema and WPS scraping feasibility are validated by Architect |
| No duplicate events in calendar | Duplicate events per sync cycle | 0 |
| No accidental deletion of personal events | Events deleted by "remove" command are exclusively tool-created ones | 0 personal events deleted |
| WPS timetable available in calendar | Timetable entries synced per zjazd | TBC — confirmed once WPS parsing is validated |
| Fast enough to set up | Time for a CS student with no Google Cloud experience to complete setup from README | ≤ 30 minutes |
| Validated by real external users | At least 2 eksternistyczne cohort students (beyond the 4 creators) complete a full calendar sync and provide feedback via Discord | Pass / Fail — minimum 2 responses collected and reviewed by creators |

> ⚠️ **Note:** Coverage metrics are TBC until the Architect validates what is reliably extractable from PUW ICS and WPS.

---

## 3. Users

- **Primary user (MVP):** Eksternistyczne (*external/extramural*) part-time AHE students — specifically the CS year cohort.
- **MVP distribution:** First to the 4 CS student creators (dogfood), then distributed to the CS year cohort via **Discord and a GitHub repository link**. Feedback collected via Discord by **Dariusz Lorenz**.
- **Secondary user:** None identified at this stage.
- **User pain today:** Logging into PUW and WPS separately, no push notifications, manually copying zjazd timetables and deadlines into personal calendars, missing last-minute lecturer posts.

> **Note:** Zaoczne students have been explicitly descoped from v1. If post-MVP feedback shows demand from zaoczne, their access pattern should be validated separately before expanding the persona.

---

## 4. Scope — MVP

### 4.1 Technology Stack

- **Runtime & language:** Python 3.10+.
- **Installation:** To be confirmed by Architect — options include `pip install ahe-sync`, `pipx install ahe-sync`, or clone-and-run. See Section 7.
- **OS support for MVP:** Windows, macOS, and Linux. The tool must work on all three without requiring platform-specific workarounds.
- **Scheduling:** No OS-level cron or Task Scheduler. The daemon runs as a long-lived Python process with an **internal scheduler** (PUW: every 10 minutes; WPS: 12:00 and 21:00 CET, `Europe/Warsaw`).
- **Mode:** Single mode only — **daemon**. There is no interactive CLI mode. All configuration is via `.env` file.

---

### 4.2 Deployment Model & Open Source

The tool is MIT-licensed and runs as a **local daemon** on the student's own machine. There is one usage model:

1. Student installs the tool (method confirmed by Architect — see Section 7).
2. Student creates a `.env` file with all required credentials and config.
3. Student starts the daemon — the process runs indefinitely with an internal scheduler syncing PUW and WPS automatically.
4. The student stops the process when they no longer need it.

**All configuration and credentials live in the `.env` file.** There are no interactive prompts. The `.env` file is plaintext — the README must include a clear security warning: never commit it to version control, restrict file permissions to the owning user.

**Documentation standard:** All documentation written in Markdown following *Docs for Developers* principles — task-oriented, code examples for every step, explicit prerequisites. Target: a student can complete setup and have the daemon running in **≤ 30 minutes**.

---

**Google OAuth — dual-path model:**

The tool supports two authorisation paths. The **shared app** is the default. The **per-user** path is the advanced option for privacy-conscious users and forks.

*Path A — Shared team app (default):*
- The team publishes one Google OAuth 2.0 application. Students authorise it via a one-time browser consent flow — no Google Cloud account required.
- The shared app's Client ID is in the repository. The Client Secret is held by the team and **never committed**.
- After consent, the student's access and refresh tokens are stored **locally in a file on their own machine**. No tokens transmitted to the team.
- ⚠️ **Verification status under investigation** — see Section 7 and Section 9.

*Path B — Per-user self-registered app (advanced / forks):*
- Students supply their own Client ID and Client Secret via `.env`.
- Tokens stored locally. No dependency on the team's app.
- Mandatory for all third-party forks.

**Demo hosted instance:**
- Runs as the daemon using Mateusz Pietrusński's account with documented explicit consent.
- Uses the shared team OAuth app. No other student's credentials should be used.
- Clearly labelled as demonstration only.

**License:** MIT. Third-party forks accepted. Forks must use OAuth Path B.

---

### 4.3 Repository & Connector Architecture

PUW and WPS are implemented as **two separate connector modules within a single Python repository**. The architecture has the following layers:

**Shared core (always required):**
- `.env` file loading and validation
- Google OAuth authorisation flow and token management (stored locally in a token file)
- Google Calendar event tagging mechanism (Section 4.6)
- Internal scheduler (PUW: every 10 min; WPS: 12:00 and 21:00 CET, `Europe/Warsaw`)
- Terminal logging output formatter

**PUW connector module (optional):**
- PUW authentication via Moodle web services (`POST /login/token.php` → `wstoken`)
- Monthly calendar fetching via `core_calendar_get_calendar_monthly_view` (current month + 2 months ahead)
- PUW-specific event type mapping and Google Calendar event construction
- Event state tracking by Moodle `event.id` (integer)
- Enabled by providing PUW credentials in `.env`; disabled if absent

**WPS connector module (optional):**
- WPS authentication via JWT (`POST /api/Profil/zaloguj` → bearer token)
- Timetable fetching via `GET /api/PlanyZajec/GETPlanSzczegolowy` for current academic semester
- WPS-specific schedule mapping and Google Calendar event construction
- Event state tracking by `IDPlanZajecPoz` (stable integer)
- Enabled by providing WPS credentials in `.env`; disabled if absent

**"Independently usable" means:** a student who omits WPS credentials from `.env` runs only PUW sync, and vice versa. No other configuration change is required.

---

### 4.4 PUW Connector — In Scope

**Authentication:** `POST /login/token.php?username=&password=&service=moodle_mobile_app` → returns `MoodleAuthTokenResponse.token` (`wstoken`). Pass as query param `wstoken` on all subsequent calls.

**Data fetch:** `POST /webservice/rest/server.php?wsfunction=core_calendar_get_calendar_monthly_view&moodlewsrestformat=json` with `year` and `month` params. On each sync cycle, fetch **3 months**: current month, next month, and the month after.

**Event deduplication:** By `MoodleCalendarEvent.id` (integer). No ICS snapshot diffing required — the API provides stable numeric IDs.

**Event type mapping** (confirmed from `MoodleCalendarEvent.eventtype` and `modulename`):

| `eventtype` | `modulename` | Google Calendar treatment |
|---|---|---|
| `meeting_start` | `clickmeeting` | Timed event — `timestart` to `timestart + timeduration` |
| `due` | `assign` | All-day event on the due date (`timestart` date) |
| `open` | `quiz` | Timed event — exam window open timestamp |
| `close` | `quiz` | Timed event — exam window close timestamp (merge with `open` into single event) |
| `attendance` | — | Timed event — include if `timeduration > 0`, skip if point-in-time |

**Sync behaviour:**
- **Create:** Event `id` not yet tagged in Google Calendar → create new event.
- **Update:** Event `id` exists in Google Calendar but `timemodified` has changed → update existing event.
- **Delete:** Event `id` was previously synced but is absent from current API response for the 3-month window → delete Google Calendar event.

**Per-event data written to Google Calendar:**
- Title: `MoodleCalendarEvent.course.fullname` + `activityname`
- Description: `activitystr`, direct link via `MoodleCalendarEvent.viewurl`
- Time: `timestart` to `timestart + timeduration` (timed); date-only for `due` type
- Optional: configurable reminder lead time per event type
- Optional: colour label per course (configured via config / env var)

**Minimum polling interval: 10 minutes** — enforced in code.

---

### 4.5 WPS Connector — In Scope

**Authentication:** `POST https://wpsapi.ahe.lodz.pl/api/Profil/zaloguj` → returns `WpsAuthTokenResponse.access_token` (JWT bearer). Pass as `Authorization: Bearer <access_token>`. Student ID for subsequent queries is decoded from the JWT payload field `id`.

**Data fetch:** `GET /api/PlanyZajec/GETPlanSzczegolowy` with params:
- `CzyNieaktywnePlany=0`
- `DataOd=<semester start date>` / `DataDo=<semester end date>` — **fixed to the current academic semester**
- `StudentID=<id from JWT>`
- `loader=none`

**Event deduplication:** By `WpsPlanSzczegolowy.IDPlanZajecPoz` (stable integer ID per schedule entry). No HTML snapshot diffing required.

**Polling schedule: twice daily at 12:00 CET and 21:00 CET** — fixed, internal scheduler in daemon mode.

**Sync behaviour:**
- **Create:** `IDPlanZajecPoz` not yet tagged in Google Calendar → create new event.
- **Update:** `IDPlanZajecPoz` exists in Google Calendar but any field (room, time, teacher) has changed → update existing event.
- **Delete:** `IDPlanZajecPoz` was previously synced but is absent from current API response → delete Google Calendar event.

**Per-event data written to Google Calendar:**
- Title: `WpsPlanSzczegolowy.PNazwa` + `TypZajec` (e.g. "Programowanie obiektowe 1 — Laboratorium")
- Description:
  - If `Webinar: false` → `SalaNumer`, `SalaAdres`, teacher names from `Dydaktyk[].ImieNazwisko`
  - If `Webinar: true` → "Online (Webinar)", teacher names from `Dydaktyk[].ImieNazwisko`
- Time: `DataOD` to `DataDO` (ISO datetime strings, CET-aware)
- Optional: configurable reminder

---

### 4.6 Event Tagging & Safe Deletion

All events written to the primary Google Calendar by this tool **must be tagged** using Google Calendar API extended properties. This tag is the sole mechanism for identifying tool-created events. Events without this tag are **never touched under any circumstances.**

- Each event is tagged with a tool identifier and a source identifier (`puw` or `wps`).
- `ahe-sync remove --source puw`: deletes all **future** Google Calendar events tagged as PUW-sourced.
- `ahe-sync remove --source wps`: deletes all **future** Google Calendar events tagged as WPS-sourced.
- **Past events (already elapsed) are intentionally never deleted** — they remain in the student's calendar permanently as a historical record after uninstall.
- The tool never reads or modifies any event it did not create.

---

### 4.7 Observability — Terminal Logging

There is no UI for MVP. The tool outputs structured logs to stdout for every sync run:

- Timestamp, source (PUW / WPS), and run type (scheduled / manual)
- Count of events created / updated / deleted
- Each error: timestamp, source, error class, human-readable message, and **suggested user action**
- On clean run: a single summary confirmation line

The Architect defines the expected user recovery action per error class in Section 7. The team defines the log format in Section 8.

---

### 4.8 Out of Scope (v1)

- Graphical UI of any kind
- WPS exam schedule (deferred post-MVP)
- Mobile native app
- Multi-user / shared calendar support
- Push notifications or alerts outside Google Calendar
- Editing events from within the tool
- Support for platforms other than PUW and WPS
- Publicly hosted SaaS or shared-credential deployment for personal use
- Zaoczne student persona

---

## 5. User Stories

| As a…                     | I want to…                                                                  | So that…                                                           |
|---------------------------|-----------------------------------------------------------------------------|--------------------------------------------------------------------|
| Eksternistyczne student   | Have new PUW events appear in my Google Calendar automatically              | I don't miss deadlines or sessions posted at short notice          |
| Eksternistyczne student   | Have rescheduled PUW events updated in my calendar automatically            | I don't show up at the wrong time for a rescheduled session        |
| Eksternistyczne student   | Have cancelled PUW events removed from my calendar automatically            | My calendar doesn't show ghost events that no longer exist         |
| Eksternistyczne student   | See submission deadlines as all-day events on their due date                | I can plan my work without re-reading the platform                 |
| Eksternistyczne student   | See my zjazd timetable from WPS in my Google Calendar                      | I have my full schedule in one place                               |
| Eksternistyczne student   | Have updated WPS timetable entries reflected in my calendar                 | Room or time changes don't catch me off guard on the zjazd day    |
| Eksternistyczne student   | Run a command to remove all future PUW or WPS events from my calendar      | I can cleanly reset my calendar without manual cleanup             |
| Eksternistyczne student   | Know from terminal output whether the last sync succeeded                   | I don't have to guess whether the daemon is working               |
| Eksternistyczne student   | Understand from an error message what went wrong and what to do             | I can fix auth or config issues without digging through code       |
| Eksternistyczne student   | Configure reminders per event type in a `.env` file                         | I get notified before important deadlines or exam windows          |
| Eksternistyczne student   | Colour-code events by subject via `.env` file                               | I can visually distinguish subjects at a glance                    |
| CS student (setup)        | Create a `.env` file and start the daemon in ≤ 30 minutes                  | I don't need to be an expert to get automated sync running         |
| CS student (exit)         | Run a remove command to clear synced events from my calendar                | I can cleanly reset without manual cleanup                         |

---

## 6. Integrations & External Systems

| System | Has API? | Auth Method | Confirmed Endpoints |
|--------|----------|-------------|---------------------|
| Google Calendar | Yes | OAuth 2.0 (per-user or shared team app) | Standard Google Calendar API v3 |
| PUW / Moodle (platforma.ahe.lodz.pl) | **Yes — confirmed** | `wstoken` via `POST /login/token.php` | `POST /webservice/rest/server.php?wsfunction=core_calendar_get_calendar_monthly_view` |
| WPS (wpsapi.ahe.lodz.pl) | **Yes — confirmed** | JWT bearer via `POST /api/Profil/zaloguj` | `GET /api/PlanyZajec/GETPlanSzczegolowy` |

**No AHE permission outreach required.** Both PUW and WPS expose documented REST APIs. Using a student's own credentials against these endpoints is equivalent to logging in as a student — no scraping, no ToS concern beyond normal fair-use of the student's own account. The ToS risk item has been removed from Section 9.

---

## 7. Open Questions for Architect

> ⬜ Primary Architect handoff. Items marked ✅ are resolved by the confirmed API type definitions.
> **Architect owner:** *To be named by the team — assign before build sprint kick-off.*
> **Deadline for remaining responses:** End of March 2026. Unresolved items are marked `🔲` in BDD scenarios.

**Technology & deployment:**
- [ ] **Python packaging:** Recommend the installation method — `pip install ahe-sync`, `pipx install ahe-sync`, or clone-and-run with `python -m ahe_sync`. Define `pyproject.toml` / `setup.cfg` entry point, minimum Python version (3.10+), and key dependencies (`requests`, `APScheduler` or equivalent, `google-api-python-client`, `python-dotenv`).
- [ ] **Internal scheduler (daemon):** Recommend a Python scheduling library (`APScheduler`, `schedule`, or custom `threading.Timer`-based) for PUW sync every 10 minutes and WPS sync at 12:00 and 21:00 CET using `Europe/Warsaw` timezone. Scheduler must be restart-stable and not drift.
- [ ] **Google OAuth token storage:** Define how the access/refresh token is persisted locally after the one-time browser consent flow — options: `token.json` file in the tool's config directory, OS keychain via `keyring`. Token file must never be committed to version control.
- [ ] **`.env` schema:** Define all required and optional keys, naming conventions (e.g. `PUW_USERNAME`, `WPS_USERNAME`, `GOOGLE_CLIENT_ID`), validation rules, and defaults. Specify whether non-credential settings (reminder lead times, colour codes) live in `.env` or a separate config file.
- [ ] **Credentials security:** Confirm plaintext `.env` is acceptable with documented file-permission hardening and `.gitignore` enforcement in README.
- [ ] **Shared OAuth app — verification feasibility:** Investigate Google's verification requirements for `calendar.events` write scope. Report: (a) required documentation, (b) student-project approval likelihood, (c) review timeline, (d) whether unverified warning is dismissible or a hard block.
- [ ] **Shared OAuth app — Client Secret protection:** Define how the Client Secret is provided at runtime without being committed or bundled in the package. Recommend an approach.

**PUW connector — ✅ resolved by `moodle-auth.types.ts` and `moodle-calendar.types.ts`:**
- ✅ Auth flow: `POST /login/token.php?username=&password=&service=moodle_mobile_app` → `wstoken`
- ✅ Full event schema confirmed: `MoodleCalendarEvent` with `id`, `timestart`, `timeduration`, `timemodified`, `eventtype`, `modulename`, `course.fullname`, `activityname`, `viewurl`
- ✅ Deduplication: by `MoodleCalendarEvent.id` (integer) — no ICS UID fallback needed
- ✅ Change detection: compare `timemodified` timestamp on re-fetched events
- ✅ Deletion detection: event `id` present in local state but absent from 3-month API response → delete
- [ ] **Moodle API rate limits:** Confirm whether `core_calendar_get_calendar_monthly_view` has any rate-limiting at 3 calls per 10-minute cycle. Test against the live instance.
- [ ] **`attendance` eventtype handling:** `eventtype: "attendance"` events appear in the type definitions. Define whether these should be synced, and if so, how they should be rendered in Google Calendar.
- [ ] **`timeduration: 0` handling:** Some events are point-in-time (`timeduration = 0`). Define Google Calendar treatment — 0-duration event, or 1-hour default, or skip?

**WPS connector — ✅ resolved by `wps-auth.types.ts` and `wps-plan-szczegolowy.types.ts`:**
- ✅ Auth flow: `POST /api/Profil/zaloguj` → `access_token` (JWT bearer); student `id` decoded from JWT payload
- ✅ Full schedule schema confirmed: `WpsPlanSzczegolowy` with `IDPlanZajecPoz`, `DataOD`, `DataDO`, `PNazwa`, `TypZajec`, `SalaNumer`, `SalaAdres`, `Dydaktyk[]`, `Webinar`
- ✅ Deduplication: by `IDPlanZajecPoz` (stable integer) — no HTML snapshot diffing needed
- ✅ Webinar handling: `Webinar: true` → `SalaNumer` and `SalaAdres` are `null` → description shows "Online (Webinar)"
- [ ] **Semester date boundaries:** How does the tool determine `DataOd` / `DataDo` for the current academic semester? Options: (a) hardcoded semester calendar in config, (b) derived from the first/last `Data` field in a prior WPS response, (c) configurable by student. Recommend an approach.
- [ ] **JWT token expiry:** `WpsJwtPayload.exp` indicates token lifetime (~6 hours per `expires_in: 21599`). Define the refresh strategy for daemon mode — re-authenticate before expiry, or on first 401 response?
- [ ] **WPS API rate limits:** Confirm whether `GETPlanSzczegolowy` has rate-limiting at twice-daily polling.
- [ ] **`NazwaGrupy` usage:** Some entries have a non-empty `NazwaGrupy` (e.g. "TECH"). Define whether this should appear in the Google Calendar event description.

**Event tagging:**
- [ ] Confirm that Google Calendar API extended properties support a persistent, queryable tag for bulk operations. Recommend the field name and value format (e.g. `ahe-sync-source: "puw"`, `ahe-sync-id: "<moodle_event_id>"`).

**Error handling & recovery:**
- [ ] **Auth failure (PUW — invalid `wstoken`):** Tool behaviour and student recovery action.
- [ ] **Auth failure (WPS — expired JWT):** Re-authentication flow — automatic or prompted?
- [ ] **Auth failure (Google OAuth — expired refresh token):** Re-authorisation CLI flow.
- [ ] **Network failure (platform unreachable):** Retry in-run or skip to next cycle?
- [ ] **HTTP 429 rate-limit hit:** Back off and retry, or skip current cycle?
- [ ] **Google Calendar API failure — per-event atomicity:** PM decision is per-event state tracking. If 5 events are being synced and 2 Calendar API writes fail, local state is updated only for the 3 that succeeded. The 2 failures are retried on the next cycle. Confirm implementability and define duplicate-prevention on retry.

> 🏗️ *Architect: please fill in feasibility, approach, and constraints for each open item above.*

---

## 8. Developer Experience (DX) — Team to Decide

> Not blocked on an external designer. Resolve during implementation planning.

- [ ] **Entry point:** Confirm the command students run to start the daemon — proposed: `ahe-sync` (if installed via pip/pipx) or `python -m ahe_sync` (if cloned). Team to confirm based on Architect's packaging recommendation.
- [ ] **First-run OAuth flow:** On first start, if no token file is found, the daemon opens a browser for Google OAuth consent, completes the localhost callback, saves the token file, then begins normal scheduling. Define behaviour if browser cannot open automatically (print URL to terminal for manual navigation).
- [ ] **Graceful shutdown:** Define the signal handling — `CTRL+C` / `SIGTERM` should stop the daemon cleanly with a log line: `"Daemon stopped."`. No partial sync state should be left inconsistent.
- [ ] **Success log format:** Proposed: `[2026-04-01 12:00:01 CET] [PUW] ✓ 2 created, 0 updated, 1 deleted`. Team to confirm.
- [ ] **Error log format:** Must include: timestamp, source, error class, human-readable message, suggested user action. Team to define.
- [ ] **`.env` missing at startup:** Daemon exits immediately with a clear message listing missing required fields — no partial startup.

---

## 9. Risks & Assumptions

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Tool accidentally deletes a personal calendar event | Low | High | Event tagging (Section 4.6) is non-negotiable; automated test coverage required for all delete operations |
| RODO (Polish GDPR) — student credentials processed locally | Medium | High | Credentials never transmitted to project team; documented in README; MIT licence — each user is responsible for their own deployment |
| Demo account (Mateusz Pietrusński) consent not formally documented | Low | High | Consent must be documented in the repository before the demo instance is made public |
| Google OAuth app not verified — "unverified app" warning | Unknown | High | **Investigation required — owner: Architect, deadline: end of March 2026.** Document warning in README; assess whether CS cohort is deterred |
| Shared OAuth app Client Secret exposed in repository | Low | High | Client Secret must never be committed; Architect to define protection mechanism before shared app is published |
| Moodle `wstoken` expires mid-daemon-run | Medium | Medium | Define re-authentication strategy; `privatetoken` in auth response can regenerate `wstoken` without re-prompting |
| WPS JWT expires mid-daemon-run (~6 hour lifetime) | Medium | Medium | Architect to define: re-authenticate proactively before expiry or reactively on 401 |
| Moodle API rate-limits 3-month calendar fetch at 10-minute intervals | Unknown | Medium | Test against live instance before build; reduce fetch window or stagger requests if needed |
| Semester date boundaries for WPS are unknown at runtime | Medium | Medium | Architect to define how `DataOd`/`DataDo` are determined; fallback: configurable in `.env` |
| Students' machines are off — daemon doesn't run, sync missed | Medium | Medium | Document this limitation clearly; recommend leaving machine on or using a home server/Raspberry Pi; out of scope to solve in v1 |
| Fewer than 2 cohort students respond with feedback | Medium | Medium | **Owner: Dariusz Lorenz.** Actively follow up via Discord |
| `attendance` eventtype handling undefined | Low | Low | Architect to define; safe default is to skip attendance events in v1 |

---

## 10. MVP Definition of Done

v1 is complete when **all of the following are true:**

1. **PUW connector:** Create, update, and delete sync work correctly for all three event types (lecture/meeting, deadline, exam).
2. **WPS connector:** Zjazd timetable create, update, and delete sync work correctly, running on the twice-daily schedule (12:00 CET and 21:00 CET).
3. **Safety:** No personal calendar events are deleted during any sync or remove operation. Verified by automated tests.
4. **Observability:** Terminal logging reports each sync run outcome with actionable error messages per the format agreed in Section 8.
5. **Daemon operation:** The daemon starts from a `.env` file, completes Google OAuth on first run, and syncs PUW and WPS continuously on schedule without manual intervention on Windows, macOS, and Linux.
6. **Setup documentation:** README written to *Docs for Developers* standard, in Markdown. A student with no prior setup experience can have the daemon running in **≤ 30 minutes**. Validated by at least one person who was not the author.
7. **External validation:** Tool distributed to CS year cohort via Discord and GitHub link. At least **2 eksternistyczne cohort students** (beyond the 4 creators) complete a full calendar sync covering at least one zjazd cycle and submit feedback via Discord. Feedback reviewed and signed off by creators. **Owner: Dariusz Lorenz.**

Items explicitly excluded from the definition of done: graphical UI, WPS exam schedule, hosted demo quality, acting on cohort feedback.

---

## 11. BDD Scenarios

> Written in Gherkin. These scenarios define the expected behaviour of the system at integration boundaries. They are the basis for acceptance tests and serve as the shared language between Product and Engineering.
>
> **Status:** v1.2 — Mode A feature removed entirely. Mode B renamed to "Daemon". OAuth consent flow updated to daemon-only context with token file reuse scenario. Remove feature updated to remove Mode A prompt reference. Shutdown scenario added. Python daemon language reflected throughout.
>
> **Out of scope for v1 BDD:** Behaviour when a student manually edits a synced event is explicitly descoped. The tool overwrites all tool-tagged event fields on each sync cycle. Manual edits to synced events will be silently overwritten. Students should not edit synced events directly — this will be documented in the README.

---

### Feature: PUW Calendar Sync

```gherkin
Feature: PUW calendar sync
  As an eksternistyczne student
  I want PUW events to be automatically reflected in my Google Calendar
  So that I never have to manually check the platform for new deadlines or sessions

  Background:
    Given the student has completed setup and Google OAuth authorisation
    And the PUW connector is enabled in the config file
    And the student's Google Calendar is accessible via the Google Calendar API

  # --- Event creation (timed event types only) ---
  # Note: submission deadline is a separate all-day event type and cannot share
  # Then steps with timed events. It has its own standalone scenario below.
  # The lecturer field in the Examples table reflects expected ICS schema output —
  # pending Architect confirmation (Section 7: PUW ICS schema question).

  Scenario Outline: New timed PUW event is added to Google Calendar
    Given a new "<event_type>" event exists on PUW with the following data:
      | field       | value            |
      | subject     | <subject>        |
      | lecturer    | <lecturer>       |
      | start       | <start>          |
      | end         | <end>            |
      | link        | <link>           |
    And the event is not yet present in Google Calendar
    When the PUW sync runs
    Then a Google Calendar event is created with title "<subject>"
    And the event start time is "<start>" and end time is "<end>"
    And the event description contains "<lecturer>" and "<link>"
    And the event is tagged with source "puw" in its extended properties

    Examples:
      | event_type  | subject           | lecturer       | start                | end                  | link                                       |
      | lecture     | Bazy Danych       | dr Kowalski    | 2026-04-05 10:00 CET | 2026-04-05 11:30 CET | https://platforma.ahe.lodz.pl/mod/url/1    |
      | online exam | Sieci Komputerowe | dr Wiśniewska  | 2026-04-20 10:00 CET | 2026-04-20 12:00 CET | https://platforma.ahe.lodz.pl/mod/quiz/3   |

  Scenario: New PUW submission deadline is created as an all-day event on the due date
    Given a submission task exists on PUW with due date "2026-04-15"
    And the task is not yet present in Google Calendar
    When the PUW sync runs
    Then a Google Calendar all-day event is created on "2026-04-15"
    And the event is not created as a timed event

  # --- First sync ---

  Scenario: First PUW sync with no prior local state adds all fetched events
    Given the PUW connector has never run before and no local event state exists
    And the Moodle API returns the following 3 events for the current 3-month window:
      | id   | subject                 | type                | start                | end                  |
      | 1001 | Bazy Danych — wykład 1  | lecture             | 2026-04-05 10:00 CET | 2026-04-05 11:30 CET |
      | 1002 | Programowanie — projekt | submission deadline | 2026-04-15 00:00 CET | 2026-04-15 23:59 CET |
      | 1003 | Sieci — egzamin         | online exam         | 2026-04-20 10:00 CET | 2026-04-20 12:00 CET |
    When the PUW sync runs
    Then 3 new Google Calendar events are created matching the above subjects and times
    And the local state is updated to record Moodle event IDs 1001, 1002, 1003 as synced

  # --- Updates ---

  Scenario: Rescheduled PUW event has its time updated in Google Calendar
    Given a PUW lecture "Bazy Danych" was previously synced with start time "09:00 CET"
    And the event on PUW now has start time "10:30 CET"
    When the PUW sync runs
    Then the existing Google Calendar event start time is updated to "10:30 CET"
    And no duplicate event is created

  Scenario: Renamed PUW event has its title updated in Google Calendar
    Given a PUW lecture was previously synced with title "Bazy Danych — wykład 1"
    And the event on PUW now has title "Bazy Danych — wykład 2"
    When the PUW sync runs
    Then the existing Google Calendar event title is updated to "Bazy Danych — wykład 2"
    And no duplicate event is created

  Scenario: Updated PUW event description is propagated to Google Calendar
    Given a PUW task was previously synced with description "Projekt 1 — wstępny zarys"
    And the event on PUW now has description "Projekt 1 — pełna dokumentacja"
    When the PUW sync runs
    Then the existing Google Calendar event description is updated to contain "Projekt 1 — pełna dokumentacja"
    And no duplicate event is created

  # --- Deletion ---

  Scenario: Cancelled PUW event is removed from Google Calendar
    Given a PUW event "Bazy Danych — wykład 3" was previously synced to Google Calendar
    And the event no longer exists on PUW
    When the PUW sync runs
    Then the Google Calendar event "Bazy Danych — wykład 3" is deleted
    And all other calendar events remain untouched

  # --- Deduplication ---

  Scenario: PUW sync does not create duplicate events for unchanged events
    Given a PUW event "Sieci Komputerowe — wykład 1" was previously synced to Google Calendar
    And the event still exists on PUW with no changes
    When the PUW sync runs
    Then no new Google Calendar event is created for "Sieci Komputerowe — wykład 1"
    And the existing event remains unchanged

  # --- Poll interval enforcement ---

  Scenario: PUW sync rejects a poll interval below the 10-minute minimum
    Given the config file specifies a PUW poll interval of "5" minutes
    When the tool validates the config at startup
    Then the tool exits with error message "PUW poll interval must be at least 10 minutes"
    And no scheduled job is installed
```

---

### Feature: WPS Calendar Sync

```gherkin
Feature: WPS timetable sync
  As an eksternistyczne student
  I want my zjazd timetable from WPS to appear in my Google Calendar
  So that I have my full schedule in one place without manually copying it

  Background:
    Given the student has completed setup and Google OAuth authorisation
    And the WPS connector is enabled in the config file
    And the student's Google Calendar is accessible via the Google Calendar API

  # --- First sync ---

  Scenario: First WPS sync with no prior local state adds all timetable sessions
    Given the WPS connector has never run before and no local event state exists
    And the WPS API returns 4 sessions for the current semester:
      | IDPlanZajecPoz | subject       | start                | end                  | room | building  | lecturer      |
      | 5001           | Bazy Danych   | 2026-04-18 09:00 CET | 2026-04-18 12:00 CET | 101  | Sterlinga | dr Kowalski   |
      | 5002           | Programowanie | 2026-04-18 13:00 CET | 2026-04-18 16:00 CET | 102  | Sterlinga | dr Nowak      |
      | 5003           | Sieci         | 2026-04-19 09:00 CET | 2026-04-19 11:00 CET | 205  | Rewolucji | dr Wiśniewska |
      | 5004           | Algorytmy     | 2026-04-19 12:00 CET | 2026-04-19 15:00 CET | 205  | Rewolucji | dr Zając      |
    When the WPS sync runs
    Then 4 Google Calendar events are created
    And the event for "Bazy Danych" has start "2026-04-18 09:00 CET", end "2026-04-18 12:00 CET", and description containing "room 101, Sterlinga, dr Kowalski"
    And each event is tagged with source "wps" in its extended properties
    And the local state is updated to record IDPlanZajecPoz 5001, 5002, 5003, 5004 as synced

  # --- Updates ---

  Scenario: Updated WPS session room is reflected in Google Calendar
    Given a WPS session "Bazy Danych" was previously synced with room "101" in building "Sterlinga"
    And the WPS timetable now shows room "205" for "Bazy Danych"
    When the WPS sync runs
    Then the existing Google Calendar event description for "Bazy Danych" is updated to contain "room 205"
    And no duplicate event is created

  Scenario: Rescheduled WPS session time is updated in Google Calendar
    Given a WPS session "Programowanie" was previously synced with start time "13:00 CET"
    And the WPS timetable now shows start time "14:00 CET" for "Programowanie"
    When the WPS sync runs
    Then the existing Google Calendar event start time for "Programowanie" is updated to "14:00 CET"
    And no duplicate event is created

  # --- Deletion ---

  Scenario: Cancelled WPS session is removed from Google Calendar
    Given a WPS session "Algorytmy" was previously synced to Google Calendar
    And "Algorytmy" no longer appears in the WPS timetable
    When the WPS sync runs
    Then the Google Calendar event "Algorytmy" is deleted
    And all other calendar events remain untouched

  # --- Schedule ---

  Scenario: WPS sync jobs are installed at the fixed twice-daily times
    Given the student has a valid config file with the WPS connector enabled
    When the student runs "ahe-sync setup"
    Then exactly two WPS sync scheduled jobs are installed
    And one job is scheduled at "12:00 CET"
    And one job is scheduled at "21:00 CET"
    And no additional WPS sync jobs are installed
```

---

### Feature: Event Tagging and Safe Deletion

```gherkin
Feature: Event tagging and safe deletion
  As an eksternistyczne student
  I want to be able to remove all synced events cleanly
  So that I can uninstall the tool without losing personal calendar entries

  Background:
    Given the following events exist in the student's primary Google Calendar:
      | event title         | source | timing |
      | Bazy Danych         | puw    | future |
      | Programowanie       | puw    | future |
      | Algorytmy (past)    | puw    | past   |
      | Sieci Komputerowe   | wps    | future |
      | Projekt końcowy     | wps    | future |
      | Urodziny mamy       | personal | future |
      | Wizyta u lekarza    | personal | future |

  Scenario: Remove command deletes only future PUW-tagged events
    When the student runs "ahe-sync remove --source puw"
    Then "Bazy Danych" and "Programowanie" are deleted from Google Calendar
    And "Algorytmy (past)", "Sieci Komputerowe", "Projekt końcowy", "Urodziny mamy", and "Wizyta u lekarza" remain untouched

  Scenario: Remove command deletes only future WPS-tagged events
    When the student runs "ahe-sync remove --source wps"
    Then "Sieci Komputerowe" and "Projekt końcowy" are deleted from Google Calendar
    And all PUW-tagged events and all personal events remain untouched

  Scenario: Past synced events are never deleted by the remove command
    When the student runs "ahe-sync remove --source puw"
    Then "Algorytmy (past)" remains in Google Calendar
    And only future PUW-tagged events are deleted

  Scenario: Sync never modifies a personal calendar event
    Given "Urodziny mamy" and "Wizyta u lekarza" are personal events not tagged by this tool
    When the PUW sync runs
    And the WPS sync runs
    Then "Urodziny mamy" and "Wizyta u lekarza" are not modified, updated, or deleted

  Scenario: Events created by the tool carry persistent source tags queryable via the API
    Given the PUW sync has created a calendar event for "Bazy Danych"
    When the event is retrieved via the Google Calendar API
    Then the event's extended properties include key "ahe-sync-source" with value "puw"
    And the event's extended properties include key "ahe-sync-tool" with value "ahe-calendar-connector"
```

---

### Feature: Daemon Startup and Scheduling

```gherkin
Feature: Daemon startup and internal scheduling
  As a CS student who wants continuous automated sync on an always-on machine
  I want to run the daemon with a .env file and have sync run automatically on schedule
  So that I never have to manually trigger a sync

  Scenario: Daemon starts and schedules both connectors from .env
    Given a valid .env file exists with PUW credentials, WPS credentials, and Google OAuth config
    And a valid Google OAuth token file exists from a prior authorisation
    When the student starts the daemon
    Then the daemon process starts and logs "Daemon started. PUW sync every 10 min. WPS sync at 12:00 and 21:00 CET."
    And the internal PUW scheduler fires every 10 minutes
    And the internal WPS scheduler fires at 12:00 CET and 21:00 CET
    And the process continues running without exiting

  Scenario: Daemon starts with only PUW credentials and runs only PUW sync
    Given the .env file contains PUW credentials but no WPS credentials
    When the student starts the daemon
    Then only the PUW internal scheduler is started
    And no WPS sync is attempted
    And the terminal logs "WPS connector disabled — no credentials provided."

  Scenario: Daemon validates .env at startup and exits on missing required field
    Given the .env file is missing the required field "PUW_USERNAME"
    When the student starts the daemon
    Then the process exits immediately with error "Missing required env var: PUW_USERNAME"
    And no sync is attempted

  Scenario: Daemon triggers Google OAuth browser flow on first run when no token file exists
    Given a valid .env file exists with all credentials
    And no Google OAuth token file exists on the machine
    When the student starts the daemon
    Then the tool opens a browser window to the Google OAuth consent screen
    And a local HTTP listener starts on a localhost port to receive the callback
    And after the student grants access, the token file is saved locally
    And the terminal outputs "Google authorisation successful. Daemon scheduler starting."
    And the internal schedulers begin running

  Scenario: Daemon internal scheduler fires PUW sync on time
    Given the daemon has been running for 10 minutes since the last PUW sync
    When the internal PUW scheduler fires
    Then a PUW sync cycle executes
    And the terminal outputs a PUW summary line with timestamp

  Scenario: Daemon internal scheduler fires WPS sync at 12:00 CET
    Given the current time is 12:00 CET
    When the internal WPS scheduler fires
    Then a WPS sync cycle executes
    And the terminal outputs a WPS summary line with timestamp

  Scenario: Daemon does not drift after restart
    Given the daemon was stopped and restarted
    When the process starts
    Then the internal scheduler resets to the correct intervals and wall-clock times
    And no duplicate sync cycles are triggered from the previous session

  Scenario: Daemon .env credentials are not logged or exposed in terminal output
    Given the .env file contains plaintext PUW and WPS credentials
    When the daemon runs a sync cycle
    Then no credential values appear in any terminal output line
    And the log contains only sync summary and error information

  Scenario: Daemon shuts down cleanly on SIGTERM or CTRL+C
    Given the daemon is running and mid-way through a sync cycle
    When the student sends SIGTERM or presses CTRL+C
    Then the current sync cycle completes or is safely abandoned
    And the terminal outputs "Daemon stopped."
    And no partial or corrupted event state is left behind
```

---

### Feature: Google OAuth Consent Flow

```gherkin
Feature: Google OAuth consent flow
  As a student setting up the daemon for the first time
  I want to connect my Google account once and have calendar access granted
  So that the daemon can write events to my primary Google Calendar automatically

  Scenario: OAuth flow opens browser and completes via localhost callback
    Given the daemon detects no existing token file on startup
    When the tool initiates the Google OAuth flow
    Then the tool opens a browser window to the Google consent screen
    And a local HTTP listener starts on a localhost port to receive the OAuth callback
    And after the student grants access, the callback delivers the authorisation code
    And the tool exchanges the code for an access token and refresh token
    And the token is saved to a local token file
    And the terminal outputs "Google authorisation successful."

  Scenario: OAuth flow with shared app shows unverified warning
    Given the shared team app is used (no custom Client ID in .env)
    When the Google consent screen loads in the browser
    Then the student sees the team's app name on the consent screen
    And the student may see an "unverified app" warning
    And after dismissing the warning and granting access, the token exchange completes normally

  Scenario: OAuth flow with per-user app uses student's own consent screen
    Given the student has set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env
    When the Google consent screen loads in the browser
    Then the student sees their own registered app name on the consent screen

  Scenario: OAuth flow fails gracefully if browser does not open
    Given the student's system cannot launch a browser automatically
    When the tool initiates the Google OAuth flow
    Then the terminal outputs "Open this URL in your browser to authorise: <url>"
    And the local HTTP listener continues waiting for the callback

  Scenario: Daemon reuses existing token file without re-prompting
    Given a valid token file already exists from a prior authorisation
    When the daemon starts
    Then no browser window is opened
    And the daemon proceeds directly to starting the internal schedulers
```

---

### Feature: Remove Synced Events

```gherkin
Feature: Remove synced events
  As a student who wants to clean up their calendar
  I want to remove all future synced events by source
  So that I can reset without manually deleting calendar entries

  Scenario: Remove command deletes only future PUW-tagged events
    Given there are future PUW-sourced events and personal events in the calendar
    When the student runs "ahe-sync remove --source puw"
    Then all future PUW-sourced events are deleted
    And all personal events and WPS-sourced events remain untouched
    And past PUW-sourced events remain in the calendar

  Scenario: Remove command deletes only future WPS-tagged events
    Given there are future WPS-sourced events and personal events in the calendar
    When the student runs "ahe-sync remove --source wps"
    Then all future WPS-sourced events are deleted
    And all personal events and PUW-sourced events remain untouched

  Scenario: Remove command requires a valid Google OAuth token to be present
    Given no valid token file exists on the machine
    When the student runs "ahe-sync remove --source puw"
    Then the tool outputs "No valid Google authorisation found. Run the daemon first to complete OAuth setup."
    And no calendar events are modified
```

---

### Feature: Timezone Handling

```gherkin
Feature: Timezone handling
  As an eksternistyczne student
  I want all calendar event times to be accurate in CET/CEST
  So that I attend classes at the right time regardless of what timezone my machine uses

  Background:
    Given the student has completed setup and Google OAuth authorisation
    And the PUW connector is enabled in the config file

  Scenario: PUW event times are stored in CET/CEST regardless of machine timezone
    Given the machine running the tool is set to timezone "UTC"
    And a PUW lecture exists with start time "10:00 CET" and end time "11:30 CET"
    When the PUW sync runs
    Then the Google Calendar event is created with start time "10:00 CET" and end time "11:30 CET"
    And the event does not reflect the machine's local UTC offset

  Scenario: PUW event times are stored in CET/CEST regardless of machine timezone
    Given the machine running the tool is set to system timezone "UTC"
    And the Moodle API returns a lecture with "timestart" Unix timestamp equivalent to "09:00 Europe/Warsaw"
    When the PUW sync runs
    Then the Google Calendar event is created with start time "09:00 Europe/Warsaw"
    And the event does not use the machine's UTC offset to interpret the timestamp
    And a student viewing the event in Google Calendar set to "Europe/Warsaw" sees "09:00"
```

---

### Feature: Error Handling and Observability

```gherkin
Feature: Error handling and terminal observability
  As an eksternistyczne student running the tool on a schedule
  I want clear terminal output for every sync run
  So that I know immediately whether sync succeeded and what to do if it failed

  # Note: Background is intentionally absent from this feature.
  # Individual scenarios set their own preconditions, as several
  # test degraded states where the calendar or platforms are unavailable.

  Scenario: Successful PUW sync produces a structured summary log line
    Given the PUW connector is configured and authenticated
    And the Google Calendar API is accessible
    When the PUW sync runs and completes without errors
    Then the terminal outputs exactly one summary line in the format:
      "[2026-04-01 12:00:01 CET] [PUW] ✓ 2 created, 0 updated, 1 deleted"

  Scenario: Successful WPS sync produces a structured summary log line
    Given the WPS connector is configured and authenticated
    And the Google Calendar API is accessible
    When the WPS sync runs and completes without errors
    Then the terminal outputs exactly one summary line in the format:
      "[2026-04-01 12:00:02 CET] [WPS] ✓ 4 created, 1 updated, 0 deleted"

  Scenario: PUW auth failure is reported with a recovery instruction  🔲
    # Recovery action (e.g. re-run ahe-sync auth) to be confirmed by Architect
    # PUW and WPS are separate scheduled jobs; a PUW auth failure has no effect on
    # the WPS job which runs on its own schedule and is not co-triggered here.
    Given the student's PUW session credentials have expired
    When the PUW sync is triggered by the scheduled job
    Then the terminal outputs an error line with error class "AUTH_FAILURE" and source "PUW"
    And the error message includes a suggested user action

  Scenario: Google OAuth refresh token expiry is detected before sync work begins  🔲
    # Re-authorisation command (e.g. ahe-sync auth) to be confirmed by Architect
    # OAuth token validity is checked at the start of each sync run, before any PUW/WPS work begins
    Given the student's Google OAuth refresh token has expired or been revoked
    When the PUW sync is triggered by the scheduled job
    Then the tool validates the Google OAuth token at the start of the run
    And the tool exits immediately with error class "GOOGLE_AUTH_FAILURE" before contacting PUW or WPS
    And the terminal outputs an error instructing the student to re-run "ahe-sync auth" to re-authorise
    And no events are created, updated, or deleted in this cycle

  Scenario: WPS parse failure skips WPS sync and continues PUW sync  🔲
    # Skip-and-continue behaviour to be confirmed by Architect
    Given the WPS HTML structure has changed such that the timetable table cannot be parsed
    When the WPS sync runs
    Then the terminal outputs an error line with error class "PARSE_FAILURE" and source "WPS"
    And the WPS sync is skipped for this cycle
    And the PUW sync runs independently and is not affected

  Scenario: Network failure to AHE platform is logged and the cycle is skipped  🔲
    # Retry vs skip behaviour to be confirmed by Architect
    Given the PUW platform is unreachable (connection timeout)
    When the PUW sync runs
    Then the terminal outputs an error line with error class "NETWORK_FAILURE" and source "PUW"
    And the sync cycle is skipped
    And the next scheduled sync runs normally

  Scenario: Google Calendar API failure is logged and failed events are retried next cycle
    Given the PUW sync fetches 5 events with Moodle IDs: 1001, 1002, 1003, 1004, 1005
    And the Google Calendar API successfully writes events for IDs 1001, 1002, 1003
    And the Google Calendar API returns an error for IDs 1004 and 1005
    When the PUW sync completes
    Then the terminal outputs an error line with error class "CALENDAR_API_FAILURE"
    And the error message states "2 events failed to write to Google Calendar"
    And the local state is updated to mark only IDs 1001, 1002, 1003 as synced
    And IDs 1004 and 1005 remain unsynced so they are retried on the next cycle
    And no duplicate events are created for IDs 1001, 1002, 1003 on retry because the tag check prevents it

  Scenario: Each connector logs independently in the same cycle
    Given both PUW and WPS connectors are enabled and both complete without errors
    When both syncs run in the same scheduled cycle
    Then the terminal output contains a separate summary line for PUW and a separate summary line for WPS
    And each summary line is independently labelled with its source
```

---

## 12. Deferred Items (No Commitment)

The following are deferred post-MVP. Priorities informed by cohort feedback collected by Dariusz Lorenz.

- WPS exam schedule sync (pending AHE structure analysis)
- Richer PUW event enrichment if ICS schema is insufficient
- Zaoczne student persona validation and support
- Onboarding simplification for non-CS students
- Hosted demo hardening for wider distribution

---

## Changelog

| Version | Date       | Summary of Changes |
|---------|------------|--------------------|
| v0.1    | 2026-03-16 | Initial draft — contributor inputs (Pietrusński, Purgał, Rutkowski, Lorenz) |
| v0.2    | 2026-03-16 | First review: narrowed persona; update/deletion sync; primary calendar; realistic metrics; ToS/RODO risks; credentials security; removed roadmap |
| v0.3    | 2026-03-16 | Second review: removed UI; per-user OAuth; MIT licence; 10-min poll floor; event tagging; terminal logging; DoD; PUW/WPS independent connectors; WPS state-storage question |
| v0.4    | 2026-03-16 | Third review: cohort acceptance criterion; connector architecture defined; demo scoped to real controlled account; Wiktor Purgał as AHE owner; error recovery questions; config schema to Architect; 30-min DoD criterion; WPS floor enforcement; DX section |
| v0.5    | 2026-03-16 | Fourth review: Node.js/TypeScript stack defined; Docker/CLI evaluation delegated to Architect; Windows/macOS/Linux OS scope; cron replaced with tool-managed installer; WPS schedule changed to twice-daily at 12:00 and 21:00 CET; persona narrowed to eksternistyczne only (zaoczne descoped); demo account named as Mateusz Pietrusński with consent requirement; docs standard set to Docs for Developers in MD; AHE deadline set to end of March; parallel build gate defined; feedback mechanism formalised (Discord, Dariusz Lorenz, min 2 respondents, full sync); past-event retention confirmed as intentional; distribution channel defined as Discord + GitHub |
| v0.6    | 2026-03-16 | Added Section 11: initial BDD scenarios in Gherkin covering PUW sync (create/update/delete/deduplicate/interval enforcement), WPS sync (create/update/delete/schedule), event tagging and safe deletion, setup and scheduled job installation, and error handling/observability. Scenarios dependent on open Architect questions marked 🔲. |
| v0.7    | 2026-03-16 | BDD scenarios revised following fifth PM review: fixed broken Scenario missing When step; replaced all "correct" assertions with explicit expected values; refactored three PUW event-creation scenarios into Scenario Outline with Examples table; added first-sync scenarios for PUW and WPS; added title and description update scenarios for PUW; added WPS time-change scenario; added re-run setup deduplication scenario; added timezone handling feature (CET/CEST); added Google Calendar API failure scenario; added Google OAuth token expiry scenario (🔲); removed conflicting Background from error handling feature; removed vacuous WPS interval-rejection scenario; descoped manual-edit-of-synced-event behaviour with explicit README note. |
| v0.8    | 2026-03-16 | BDD and PRD revised following sixth PM review: (1) removed submission deadline from Scenario Outline — contradiction with all-day event scenario resolved; deadline type in its own standalone scenario only; (2) Google Calendar API failure retry logic clarified as per-event snapshot update — Architect question added; (3) OAuth expiry scenario fixed — "When any sync runs" replaced with specific trigger; OAuth validation confirmed to happen before any PUW/WPS work; (4) CEST scheduler scenario replaced with application-level timezone scenario testing IANA timezone handling in ICS feed; (5) first-sync PUW scenario now uses concrete data table with UIDs; (6) PUW auth failure scenario — removed spurious WPS independence assertion with explanatory comment; (7) Section 7 — added Architect owner placeholder and end-of-March deadline; (8) Section 4.1/4.3 Docker vs CLI conflict resolved as conditional scope — scheduled job installer only applies to CLI model; (9) deadline lecturer field annotated as pending ICS schema confirmation; (10) ahe-sync status descoped from MVP in Section 8; (11) `ahe-sync uninstall` command defined in Section 8 as distinct from `remove`; three uninstall BDD scenarios added to Setup feature; uninstall user story added to Section 5. |
| v0.9    | 2026-03-16 | Google OAuth model updated to dual-path: shared team app as default (no Google Cloud account needed), per-user self-registered app as advanced option for privacy-conscious users and forks. Section 4.2 rewritten. Two Section 7 Architect questions added: OAuth app verification feasibility and Client Secret protection. Two Section 9 risks added. BDD setup OAuth scenario replaced with two path-specific scenarios. Forks required to use per-user path. |
| v1.0    | 2026-03-16 | Major architecture revision: two-mode model defined. Mode A (interactive CLI, `ahe-sync`, credentials runtime-only, one-shot) and Mode B (daemon, `npm start`, credentials via `.env`, internal scheduler). Docker and OS cron entirely removed. Installation changed to `npm install -g ahe-sync`. Sections 4.1, 4.2, 4.3, 7, 8, 10 updated throughout. User stories updated for two modes. DoD criterion 5 replaced with two-mode operation criterion; setup time split into 15 min (Mode A) and 30 min (Mode B). BDD setup feature completely rewritten: Mode A interactive flow, Mode B daemon, OAuth consent flow, remove events — cron/install-job scenarios removed. |
| v1.1    | 2026-03-16 | API types confirmed: both PUW (Moodle web services) and WPS have documented REST APIs — no HTML scraping needed. AHE permission outreach dropped entirely. Section 4.3 connector descriptions updated. Sections 4.4 and 4.5 fully rewritten with confirmed endpoints, auth flows, schemas, event type mapping table, deduplication strategy (Moodle `event.id`, WPS `IDPlanZajecPoz`), Webinar handling, and semester-date range for WPS. Section 6 updated with confirmed endpoints, AHE permission gate removed. Section 7 restructured: PUW and WPS questions closed (marked ✅) where resolved by type files; new open questions added for Moodle rate limits, `attendance` eventtype, `timeduration:0`, semester date boundary strategy, WPS JWT refresh, `NazwaGrupy` display. Section 9 risks updated: AHE ToS risk removed, WPS HTML structure risk removed, ICS auth risk removed; new API-specific risks added (wstoken expiry, JWT expiry, Moodle rate limits, semester boundary). BDD scenarios updated: ICS/snapshot/UID language replaced with Moodle event.id and WPS IDPlanZajecPoz; first-sync, timezone, and API failure scenarios updated. |
| v1.2    | 2026-03-16 | Language changed from Node.js/TypeScript to Python. Mode A (interactive CLI) removed entirely — tool is daemon-only. Entry point changed from `npm start` to Python daemon (method TBD by Architect). Sections 4.1, 4.2, 4.3 rewritten for Python daemon-only model. Section 7 packaging and scheduler questions updated for Python. Section 8 simplified to daemon-only DX. User stories updated — Mode A stories removed. DoD criterion 5 simplified to single daemon mode; setup time unified at 30 minutes. BDD: Mode A feature removed, Mode B renamed to Daemon with Python entry point, OAuth feature updated to daemon-first flow with token file reuse scenario, Remove feature updated, shutdown scenario added. |
