# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Status

This project is currently in the **design/specification phase**. There is no implementation code yet. The active work is in `docs/PRD/PRD.md` (v1.2, ready for Architect review) and the OpenSpec workflow in `openspec/`.

---

## What This Project Does

A local daemon (`ahe-sync`) written in **Python 3.10+** that automatically syncs events from two AHE university platforms into Google Calendar:

- **PUW** (`platforma.ahe.lodz.pl`) — Moodle-based e-learning platform. Authenticated via `POST /login/token.php` → `wstoken`. Events fetched from `core_calendar_get_calendar_monthly_view` (3 months ahead). Polled every 10 minutes.
- **WPS** (`wpsapi.ahe.lodz.pl`) — Academic timetable system. Authenticated via `POST /api/Profil/zaloguj` → JWT bearer. Schedule fetched from `GET /api/PlanyZajec/GETPlanSzczegolowy`. Polled at 12:00 and 21:00 CET.

Both connectors are **optional**: if credentials are absent from `.env`, that connector is skipped.

---

## Architecture

Full architecture in `docs/architecture/README.md`. ADRs in `docs/adr/`.

**Flat module structure** (ADR-0004 — full hexagonal ruled out as over-engineered for 2 connectors):

```
ahe_sync/
├── __main__.py       # Entry point + composition root (only place that wires instances)
├── config.py         # .env → Config dataclass; hard exit if invalid
├── models.py         # Shared: CalendarEvent, SyncPlan, SyncResult dataclasses
├── state.py          # Read/write ~/.config/ahe-sync/state.json (atomic writes)
├── scheduler.py      # APScheduler: IntervalTrigger (PUW) + CronTrigger (WPS, Europe/Warsaw)
├── sync_engine.py    # Pure logic: compute_diff() + apply_sync_plan(); no I/O; fully unit-testable
├── google/
│   ├── auth.py       # OAuth first-run browser flow; token.json at ~/.config/ahe-sync/
│   └── calendar.py   # create/update/delete/find_tagged_events; only touches tagged events
└── connectors/
    ├── base.py       # ConnectorBase ABC: fetch() → list[CalendarEvent]
    ├── puw.py        # Moodle wstoken auth + 3-month calendar fetch + mapping
    └── wps.py        # JWT auth (proactive refresh at exp-5min) + plan fetch + mapping
```

**Key invariant:** `sync_engine.py` only imports from `models.py`. It never imports from `connectors/` or `google/`.

---

## Key Domain Concepts

**Event tagging:** Every event written to Google Calendar is tagged using extended properties (`ahe-sync` tool identifier + source: `puw` or `wps`). The tool **never reads or modifies events it didn't create**. Past events are never deleted (historical record).

**Deduplication:**
- PUW: by `MoodleCalendarEvent.id` (integer); change detection via `timemodified`
- WPS: by `WpsPlanSzczegolowy.IDPlanZajecPoz` (stable integer)

**Google OAuth — dual-path:**
- Path A (default): shared team OAuth app — Client ID in repo, Client Secret never committed
- Path B (advanced): student supplies their own Client ID + Secret via `.env`

**Safe removal:** `ahe-sync remove --source puw|wps` deletes only future tagged events, never past ones and never personal events.

---

## Development Workflow

This project uses **OpenSpec** for spec-driven development. The workflow is:

1. `/openspec-explore` — think through ideas and clarify requirements
2. `/openspec-propose` — create a change proposal with design, specs, and tasks
3. `/openspec-apply-change` — implement tasks from a proposal
4. `/openspec-archive-change` — finalize and archive a completed change

OpenSpec config: `openspec/config.yaml`. Changes live in `openspec/changes/`, specs in `openspec/specs/`.

---

## Skills (Cursor / Claude)

| Skill | When to use |
|-------|-------------|
| `architect-persona` | System design, C4 diagrams (Mermaid), BDD/Gherkin, ADRs, PRD review |
| `node-js-best-practices` | Framework selection, async patterns, architecture decisions |
| `pm-prd` | Collaborating on or updating the PRD |

The architect persona expects: C4 diagrams before explanations, ADRs for key decisions, BDD scenarios at integration boundaries, and Hexagonal Architecture for anything touching external integrations.

---

## Key Architecture Decisions

| Decision | Resolution | Detail |
|----------|-----------|--------|
| Packaging | Clone repo + `python scripts/setup.py`; no PyPI | ADR-0001 |
| Scheduler | APScheduler 3.x | ADR-0002 |
| Token storage | Tiered: `local` (default, consent prompt on first run) / `memory` (opt-in) | ADR-0003 |
| State storage | `~/.config/ahe-sync/state.json` unconditionally (no credentials) | ADR-0003 |
| Project structure | Flat modules | ADR-0004 |
| WPS JWT refresh | Proactive: re-auth when `exp - now < 5 min` | ADR-0002 |
| WPS semester dates | Auto-detected from API; `.env` override available | `docs/architecture/README.md §8` |
| PUW `timeduration: 0` | 0-duration Google Calendar event | `docs/architecture/README.md §8` |
| PUW `attendance` events | Skip in v1 | `docs/architecture/README.md §8` |

---

## Documentation Standard

All docs follow *Docs for Developers* principles: task-oriented, code examples for every step, explicit prerequisites. Target: a CS student can complete setup and have the daemon running in ≤ 30 minutes.

ADRs go in `docs/adr/` using the template at `.cursor/skills/architect-persona/references/adr-template.md`.
