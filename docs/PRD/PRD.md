# PRD: AHE Calendar Integration

## Document Info
| Field   | Value                              |
|---------|------------------------------------|
| Version | v0.8                               |
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

- **Runtime & language:** Node.js with TypeScript.
- **Deployment:** The Architect should evaluate and recommend either a Docker-based setup or a polished CLI with an installer — whichever minimises the setup burden for a CS student on Windows, macOS, or Linux.
- **OS support for MVP:** Windows, macOS, and Linux. The tool must work on all three without requiring WSL or platform-specific workarounds from the user.
- **Cron / scheduling:** The tool installs and manages its own scheduled jobs automatically via a setup command. The student does not write cron expressions manually. See Section 4.2.

---

### 4.2 Deployment Model & Open Source

The tool is MIT-licensed and designed for **local self-hosted use**. The intended usage model is:

1. Student clones the repository (or downloads a release).
2. Student follows the step-by-step setup documentation. Target: **≤ 30 minutes** for a CS student with no prior Google Cloud experience.
3. Student runs a setup command that configures credentials, validates the config, and installs the scheduled sync jobs automatically.
4. The tool runs on schedule without further manual intervention.

**Documentation standard:** All documentation is written in Markdown and follows the principles from *Docs for Developers* — clear structure, task-oriented content, code examples for every step, and explicit prerequisite statements. No ambiguity about what the reader needs to do next.

**No graphical UI is built for MVP.** Interaction is via a config file and CLI commands. Appropriate for the CS-student target audience.

**Google OAuth — per-user model:**
- Each student registers their own Google Cloud project and OAuth 2.0 credentials (Client ID + Client Secret).
- Credentials are stored locally. No credentials are stored on any external server controlled by the project team.
- The README must include a step-by-step walkthrough for creating a Google Cloud project and OAuth consent screen, following the *Docs for Developers* standard.

**Demo hosted instance:**
- A single team-controlled demo instance is maintained for demonstration purposes.
- **Account used:** Mateusz Pietrusński's student account. Mateusz is a project creator and has given explicit, informed consent for his credentials and calendar data to be processed through the team-hosted instance for demo purposes. This consent is documented in the repository.
- The demo OAuth client is registered to the project team and must not be used in personal deployments.
- The demo instance must be clearly labelled as *not* the intended usage model. Personal use through the demo is explicitly unsupported.

**License:** MIT. Third-party forks are accepted. AHE's permission (once obtained) is specific to this project; forks are independently responsible for their own compliance.

---

### 4.3 Repository & Connector Architecture

PUW and WPS are implemented as **two separate connector modules within a single repository**. The architecture has the following layers:

**Shared core (always required):**
- Google OAuth authorisation flow and token management
- Google Calendar event tagging mechanism (Section 4.5)
- Config file loading and validation (including poll schedule enforcement)
- Terminal logging output formatter
- Scheduled job installer (`--install-cron` or equivalent)

**PUW connector module (optional):**
- PUW authentication and ICS fetching
- PUW-specific event parsing and mapping
- PUW sync state storage (previous ICS snapshot)
- Enabled or disabled independently via config

**WPS connector module (optional):**
- WPS authentication and HTML table scraping
- WPS-specific timetable parsing and mapping
- WPS sync state storage (previous HTML snapshot)
- Enabled or disabled independently via config

**"Independently usable" means:** a student who only wants PUW sync configures only the PUW block in their config file. The WPS connector is not invoked — no WPS credentials required, no WPS jobs scheduled. The shared core is always present. The connectors are not separate packages or repositories.

---

### 4.4 PUW Connector — In Scope

- Authenticate against PUW using stored credentials.
- Fetch events via the ICS export endpoint (`/calendar/export.php`).
- **Minimum polling interval: 10 minutes.** Enforced in code — the tool refuses to schedule PUW sync at a shorter interval.
- Default polling interval: 10 minutes (configurable upward via config).
- **Create:** Add new events not yet in the calendar.
- **Update:** Detect changed events and update the corresponding Google Calendar entry.
- **Delete:** Detect removed events and delete the corresponding Google Calendar entry. Only tool-tagged events may be deleted. See Section 4.5.
- Duplicate detection: match on ICS UID; fall back to title + start time + end time if UID is absent.
- Event categories mapped from PUW:
  - Online lectures / project sessions / labs — start & end time
  - Submission deadlines — all-day event on final due date
  - Online exams / quizzes — start & end time (merged from two platform timestamps where applicable)
- Per-event data written to Google Calendar:
  - Title: subject name
  - Description: lecturer name, task/topic name, direct link to platform entry
  - Time: exact start & end, or all-day for deadlines
  - Optional: configurable reminder lead time per event type
  - Optional: colour label per subject (configured via config file)

---

### 4.5 WPS Connector — In Scope

- Authenticate against WPS using stored credentials.
- Parse the zjazd timetable (plan zajęć) from the HTML table.
- **Polling schedule: twice daily at 12:00 CET and 21:00 CET.** This is the fixed default. The tool installs two scheduled jobs for WPS. No lower frequency is permitted; no shorter interval is accepted in config.
- **Create / Update / Delete** behaviour applies on each poll cycle via HTML snapshot diffing. Mechanism defined by Architect — see Section 7.
- Per-event data written to Google Calendar:
  - Title: subject name
  - Description: room, building, lecturer name
  - Time: exact start & end per session
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
| Eksternistyczne student   | Run a command to force an immediate sync                                    | I can refresh without waiting for the next scheduled run           |
| Eksternistyczne student   | Run a command to remove all future PUW or WPS events from my calendar      | I can cleanly uninstall or reset without manual cleanup            |
| Eksternistyczne student   | Know from terminal output whether the last sync succeeded                   | I don't have to guess whether the tool is working                  |
| Eksternistyczne student   | Understand from an error message what went wrong and what to do             | I can fix auth or config issues without digging through code       |
| Eksternistyczne student   | Configure reminders per event type in a config file                         | I get notified before important deadlines or exam windows          |
| Eksternistyczne student   | Colour-code events by subject via config file                               | I can visually distinguish subjects at a glance                    |
| CS student (setup)        | Run a single setup command that installs all scheduled sync jobs            | I don't have to write cron expressions manually                    |
| CS student (setup)        | Follow a step-by-step README to set up my Google OAuth app in ≤ 30 min     | I don't need prior Google Cloud experience to get started          |
| CS student (exit)         | Run an uninstall command that stops all future syncs                        | My machine isn't running background jobs after I stop using the tool |

---

## 6. Integrations & External Systems

| System | Has API? | Auth Method | Notes |
|--------|----------|-------------|-------|
| Google Calendar | Yes | OAuth 2.0 (per-user, self-registered) | Each student registers their own Google Cloud project; credentials stored locally |
| PUW (platforma.ahe.lodz.pl) | Partial | Session-based (details TBC) | ICS endpoint exists; auth requirements TBC; **AHE permission required — owner: Wiktor Purgał — deadline: end of March 2026** |
| WPS (AHE schedule system) | No | Session-based / HTML scraping | No structured export; HTML table scraping required; **AHE permission required — owner: Wiktor Purgał — deadline: end of March 2026** |

**Development gate:** While awaiting AHE permission, the team may proceed with building the shared core and Google Calendar integration layer. Development of the PUW and WPS scraping/parsing layer must not begin until AHE grants permission. If permission is denied by end of March: the team decides whether to halt, pivot to a manual-export import model, or proceed at personal risk with full documented awareness.

---

## 7. Open Questions for Architect

> ⬜ Primary Architect handoff. All items below require technical decisions before the build sprint begins.
> **Architect owner:** *To be named by the team — assign before build sprint kick-off.*
> **Deadline for Section 7 responses:** End of March 2026, aligned with the AHE permission deadline. Unresolved items block the build sprint and leave 9 BDD scenarios in `🔲` state.

**Technology & deployment:**
- [ ] **Docker vs. CLI installer:** Evaluate and recommend the deployment model (Docker container, standalone CLI binary, npm global install, or other) that achieves ≤ 30-minute setup on Windows, macOS, and Linux without platform-specific prerequisites. Document the trade-offs.

  > ⚠️ **PM note — conditional scope:** The scheduled job installer (Section 4.3 shared core) is only in scope if the **CLI model** is chosen. If Docker is chosen, scheduling is the responsibility of the host environment (e.g. host cron calling `docker run`, or Docker restart policy). The README must document the host-side scheduling setup in that case. The BDD setup scenarios (Section 11) assume CLI — they must be revised if Docker is chosen.

- [ ] **Scheduled job installer (CLI model only):** Design the cross-platform mechanism for `ahe-sync setup` to install scheduled jobs — cron on macOS/Linux, Task Scheduler or equivalent on Windows. The student must not write schedules manually.
- [ ] **Config file schema:** Define required and optional fields, format (YAML / TOML / .env / JSON), validation rules, and defaults. This is the primary user interface for MVP — it must be specified here before implementation begins.
- [ ] **Credentials security:** How should PUW, WPS, and Google OAuth credentials be stored locally? Options: OS keychain (keytar), encrypted config file, environment variables. Plaintext is not acceptable.
- [ ] **Google OAuth token storage:** How should the access/refresh token be persisted after initial authorisation on all three target OS environments?

**PUW connector:**
- [ ] Does the PUW ICS export endpoint require an authenticated session, or is a token-in-URL flow available? What is the full auth flow?
- [ ] What is the complete PUW ICS schema? Are lecturer name, task link, and event type reliably present, or will supplementary scraping be needed?
- [ ] ICS UID-based duplicate detection — implementation approach and fallback when UID is absent?
- [ ] **PUW snapshot diffing:** Where is the previous ICS snapshot stored between runs? How are changes and deletions detected reliably?
- [ ] Is there evidence of rate-limiting or bot-detection on PUW at a 10-minute polling interval?

**WPS connector:**
- [ ] Can the WPS HTML timetable table be parsed reliably across semesters and student groups? Is there a stable per-student URL pattern?
- [ ] **WPS snapshot diffing:** Where is the previous timetable state stored between runs? How are row-level changes detected (e.g. room change vs. session cancellation)?
- [ ] Is there evidence of rate-limiting or bot-detection on WPS at twice-daily polling?

**Event tagging:**
- [ ] Confirm that Google Calendar API extended properties support a persistent, tool-specific tag queryable for bulk operations. Recommend the field name and value format.

**Error handling & recovery — define tool behaviour AND expected student action for each:**
- [ ] **Auth failure (PUW or WPS session expired):** Tool behaviour? Student recovery action?
- [ ] **Auth failure (Google OAuth refresh token expired):** Re-authorisation flow from CLI?
- [ ] **Parse failure (WPS HTML structure changed):** Does the tool skip WPS and continue PUW, or halt? What does the student do while waiting for a fix?
- [ ] **Network failure (platform unreachable):** Retry in-run, or skip and wait for next scheduled cycle?
- [ ] **Rate-limit hit (HTTP 429 or equivalent):** Back off and retry, or skip current cycle?
- [ ] **Google Calendar API failure — sync cycle atomicity:** PM decision is per-event snapshot update (not all-or-nothing). If 5 events are being synced and 2 Calendar API writes fail, the snapshot is updated only for the 3 that succeeded. The 2 that failed remain in the diff on the next cycle and are retried. Confirm this is implementable and define how partial-write state is tracked without risking duplicates on retry (i.e. the retry must check for an existing tagged event before creating).

> 🏗️ *Architect: please fill in feasibility, approach, and constraints for each item above.*

---

## 8. Developer Experience (DX) — Team to Decide

> Not blocked on an external designer. Resolve during implementation planning.

- [ ] **CLI command interface:** Proposed: `ahe-sync setup`, `ahe-sync sync --source puw|wps|all`, `ahe-sync remove --source puw|wps`, `ahe-sync uninstall`. `ahe-sync status` is **descoped from MVP** — observability is covered by terminal logging from scheduled runs. Team to confirm final command set.
- [ ] **Remove vs. uninstall — distinct commands:** `ahe-sync remove --source puw|wps` clears tagged events from Google Calendar but does **not** stop future syncs. `ahe-sync uninstall` removes all installed scheduled jobs and stops future syncs, but does **not** touch the calendar. Students who want a clean exit must run both. This two-command model must be documented clearly in the README.
- [ ] **First-run flow:** How does the tool prompt the student through Google OAuth on first invocation? Browser-launched consent flow?
- [ ] **Success log format:** Proposed: `[2026-03-16 12:00:01 CET] [PUW] ✓ 2 created, 0 updated, 1 deleted`. Team to confirm.
- [ ] **Error log format:** Must include: timestamp, source, error class, human-readable message, suggested user action. Team to define.

---

## 9. Risks & Assumptions

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| AHE ToS or IT policy prohibits automated access to PUW/WPS | Unknown | **Critical** | **Owner: Wiktor Purgał. Deadline: end of March 2026.** Request permission before scraping development begins. If refused: team decides — halt, pivot to manual-export model, or proceed at personal documented risk. Shared core and Google Calendar layer may be built in parallel while waiting. |
| PUW ICS export requires active session auth | High | High | Investigate first; fallback to authenticated HTTP scraping |
| Tool accidentally deletes a personal calendar event | Low | High | Event tagging (Section 4.6) is non-negotiable; automated test coverage required for all delete operations |
| RODO (Polish GDPR) — student credentials processed locally | Medium | High | Credentials never transmitted to project team; documented in README; MIT licence — each user is responsible for their own deployment |
| Demo account (Mateusz Pietrusński) consent not formally documented | Low | High | Consent must be documented in the repository before the demo instance is made public |
| WPS HTML structure changes between polls, breaking parser | Medium | High | Log parse failures; skip WPS and continue PUW; document known-good structure version in codebase |
| AHE IP-bans the tool due to polling | Medium | High | Enforce poll minimums in code; randomise request timing slightly |
| Students' machines are off — sync doesn't run | Medium | Medium | Document clearly; out of scope to solve in v1 |
| Google OAuth consent screen shows "unverified app" warning | Low | Medium | Expected; documented in setup guide as safe for personal use with own registered app |
| Fewer than 2 cohort students respond with feedback | Medium | Medium | **Owner: Dariusz Lorenz.** Actively follow up via Discord; DoD requires minimum 2 responses |
| WPS exam schedule is not scrapeable in v1 | High | Low | Explicitly out of scope |

---

## 10. MVP Definition of Done

v1 is complete when **all of the following are true:**

1. **PUW connector:** Create, update, and delete sync work correctly for all three event types (lecture/meeting, deadline, exam).
2. **WPS connector:** Zjazd timetable create, update, and delete sync work correctly, running on the twice-daily schedule (12:00 CET and 21:00 CET).
3. **Safety:** No personal calendar events are deleted during any sync or remove operation. Verified by automated tests.
4. **Observability:** Terminal logging reports each sync run outcome with actionable error messages per the format agreed in Section 8.
5. **Scheduled job installer:** `ahe-sync setup` (or equivalent) successfully installs all scheduled jobs on Windows, macOS, and Linux without manual cron configuration by the student.
6. **Setup documentation:** README is written to *Docs for Developers* standard, in Markdown, and has been followed successfully by at least one person who was not the author, in **≤ 30 minutes**, with no prior Google Cloud experience.
7. **External validation:** Tool distributed to CS year cohort via Discord and GitHub link. At least **2 eksternistyczne cohort students** (beyond the 4 creators) complete a **full calendar sync** (covering at least one zjazd cycle) and submit feedback via Discord. Feedback reviewed and signed off by the creators. **Owner: Dariusz Lorenz.**

Items explicitly excluded from the definition of done: graphical UI, WPS exam schedule, hosted demo quality, acting on cohort feedback.

---

## 11. BDD Scenarios

> Written in Gherkin. These scenarios define the expected behaviour of the system at integration boundaries. They are the basis for acceptance tests and serve as the shared language between Product and Engineering.
>
> **Status:** v0.7 — revised following PM review. All `Then` steps use explicit expected values. Broken `When` steps fixed. Missing scenarios added: first-sync, re-run setup, title/description updates, timezone, Google Calendar API failure, Google OAuth expiry. PUW event-creation scenarios refactored into `Scenario Outline`. Scenarios marked `🔲` depend on open Architect questions (Section 7) and will be finalised once those are resolved.
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

  Scenario: First PUW sync with no prior snapshot adds all fetched events
    Given the PUW connector has never run before and no local ICS snapshot exists
    And PUW contains the following 3 events:
      | uid   | subject               | type    | start                | end                  |
      | uid-1 | Bazy Danych — wykład 1 | lecture | 2026-04-05 10:00 CET | 2026-04-05 11:30 CET |
      | uid-2 | Programowanie — projekt | submission deadline | 2026-04-15 00:00 CET | 2026-04-15 23:59 CET |
      | uid-3 | Sieci — egzamin        | online exam | 2026-04-20 10:00 CET | 2026-04-20 12:00 CET |
    When the PUW sync runs
    Then 3 new Google Calendar events are created matching the above subjects and times
    And a local ICS snapshot containing all 3 event UIDs is saved for use in the next sync cycle

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

  Scenario: First WPS sync with no prior snapshot adds all timetable sessions
    Given the WPS connector has never run before and no local HTML snapshot exists
    And the WPS timetable contains 4 sessions across 2 days:
      | subject           | start                | end                  | room | building  | lecturer     |
      | Bazy Danych       | 2026-04-18 09:00 CET | 2026-04-18 12:00 CET | 101  | Sterlinga | dr Kowalski  |
      | Programowanie     | 2026-04-18 13:00 CET | 2026-04-18 16:00 CET | 102  | Sterlinga | dr Nowak     |
      | Sieci             | 2026-04-19 09:00 CET | 2026-04-19 11:00 CET | 205  | Rewolucji | dr Wiśniewska|
      | Algorytmy         | 2026-04-19 12:00 CET | 2026-04-19 15:00 CET | 205  | Rewolucji | dr Zając     |
    When the WPS sync runs
    Then 4 Google Calendar events are created
    And the event for "Bazy Danych" has start "2026-04-18 09:00 CET", end "2026-04-18 12:00 CET", and description containing "room 101, Sterlinga, dr Kowalski"
    And each event is tagged with source "wps" in its extended properties
    And a local HTML snapshot is saved for use in the next sync cycle

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

### Feature: Setup and Scheduled Job Installation

```gherkin
Feature: Setup and scheduled job installation
  As a CS student with no prior Google Cloud experience
  I want a single setup command to configure everything
  So that I can complete setup in under 30 minutes without writing cron expressions

  Scenario: Setup command installs both PUW and WPS scheduled jobs
    Given the student has a valid config file with both connectors enabled
    And the student has completed Google OAuth authorisation
    When the student runs "ahe-sync setup"
    Then a PUW sync job is scheduled to run every 10 minutes
    And a WPS sync job is scheduled to run at "12:00 CET" and "21:00 CET"
    And the terminal outputs "Setup complete. 3 scheduled jobs installed."

  Scenario: Setup command installs only the PUW job when WPS is disabled
    Given the student has a valid config file with only the PUW connector enabled
    When the student runs "ahe-sync setup"
    Then only the PUW sync job is scheduled
    And no WPS sync job is installed
    And the terminal outputs "Setup complete. 1 scheduled job installed."

  Scenario: Re-running setup replaces existing scheduled jobs without creating duplicates
    Given the student previously ran "ahe-sync setup" and 3 scheduled jobs are installed
    And the student has updated the config file
    When the student runs "ahe-sync setup" again
    Then the existing 3 scheduled jobs are removed
    And new scheduled jobs are installed reflecting the updated config
    And the total number of installed jobs does not exceed the expected count

  Scenario: Setup command launches Google OAuth browser flow on first run
    Given the student has not yet authorised the tool with Google
    When the student runs "ahe-sync setup"
    Then the tool opens a browser window to the Google OAuth consent screen
    And after the student grants permission, the access token and refresh token are stored locally
    And the terminal outputs "Google authorisation successful."

  Scenario: Setup command fails gracefully on missing required config field
    Given the student's config file is missing the required field "puw.username"
    When the student runs "ahe-sync setup"
    Then the tool exits with error message "Missing required config field: puw.username"
    And no scheduled jobs are installed
    And no OAuth browser flow is launched

  Scenario: Uninstall command removes all scheduled jobs without touching the calendar
    Given the student has previously run "ahe-sync setup" and 3 scheduled jobs are installed
    And there are synced PUW and WPS events in the student's Google Calendar
    When the student runs "ahe-sync uninstall"
    Then all 3 scheduled sync jobs are removed from the OS scheduler
    And no future syncs will run automatically
    And all Google Calendar events (both synced and personal) remain untouched
    And the terminal outputs "Uninstall complete. All scheduled jobs removed. Your calendar was not modified."

  Scenario: Full clean exit requires both remove and uninstall commands
    Given the student wants to fully remove the tool and all its calendar entries
    When the student runs "ahe-sync remove --source puw"
    And the student runs "ahe-sync remove --source wps"
    And the student runs "ahe-sync uninstall"
    Then all future PUW and WPS events are removed from Google Calendar
    And all scheduled sync jobs are removed from the OS scheduler
    And personal calendar events and past synced events remain untouched
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
    And a PUW lecture exists in the ICS feed with DTSTART "20260405T090000" and TZID "Europe/Warsaw"
    When the PUW sync runs
    Then the Google Calendar event is created with start time equivalent to "09:00 Europe/Warsaw"
    And the event does not use the machine's UTC offset to interpret the time
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
    Given the PUW sync fetches 5 events: "uid-1", "uid-2", "uid-3", "uid-4", "uid-5"
    And the Google Calendar API successfully writes events "uid-1", "uid-2", "uid-3"
    And the Google Calendar API returns an error for events "uid-4" and "uid-5"
    When the PUW sync completes
    Then the terminal outputs an error line with error class "CALENDAR_API_FAILURE"
    And the error message states "2 events failed to write to Google Calendar"
    And the local ICS snapshot is updated to include only "uid-1", "uid-2", "uid-3"
    And "uid-4" and "uid-5" remain outside the snapshot so they are retried on the next cycle
    And no duplicate events are created for "uid-1", "uid-2", "uid-3" on retry because the tag check prevents it

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