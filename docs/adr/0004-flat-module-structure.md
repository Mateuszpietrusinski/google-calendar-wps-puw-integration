# ADR-0004: Flat Module Structure Over Full Hexagonal Architecture

**Date:** 2026-03-29
**Status:** Proposed
**Deciders:** Architect, Team
**Related ADRs:** —

---

## Context

The `architect-persona` skill defaults to Hexagonal Architecture (Ports & Adapters) for anything touching external integrations. However, `ahe-sync` is a **local daemon with two inputs and one output**:

- 2 connectors (PUW, WPS) that each return `list[CalendarEvent]`
- 1 output (Google Calendar)
- 1 piece of core logic (`sync_engine.py`: diff + apply)
- No HTTP server, no database, no plugin system, no plans for additional connectors in v1

A full hexagonal structure (`domain/`, `ports/inbound/`, `ports/outbound/`, `adapters/`) would add 3–4 directory levels and ~6 boilerplate files for two concrete adapters that will never be swapped. The overhead is not justified at this scale.

## Decision

We will use a **flat module structure** with a `connectors/` subpackage and a `google/` subpackage.

```
ahe_sync/
├── __main__.py       # wires everything; the only "composition root"
├── config.py
├── models.py         # shared dataclasses (CalendarEvent, SyncPlan, SyncResult)
├── state.py
├── scheduler.py
├── sync_engine.py    # pure functions; testable without any mocks
├── google/
│   ├── auth.py
│   └── calendar.py
└── connectors/
    ├── base.py       # ConnectorBase ABC (fetch → list[CalendarEvent])
    ├── puw.py
    └── wps.py
```

The **boundary that hexagonal would enforce via interfaces is preserved** in a lighter way:
- `sync_engine.py` only knows `models.py` types — it does not import from `connectors/` or `google/`
- `connectors/base.py` defines the `ConnectorBase` ABC — both connectors implement it
- `__main__.py` is the only place that imports everything and wires instances together

This achieves the key testability benefit of hexagonal (sync engine is pure; connectors are independently testable via fixture JSON) without the structural overhead.

## Consequences

### Positive
- All modules are discoverable in one directory listing — low cognitive overhead for new contributors.
- `sync_engine.py` is pure (no I/O), making unit tests fast and straightforward.
- Explicit wiring in `__main__.py` makes the data flow visible without hunting through dependency injection config.
- Fewer files = faster onboarding for a student project with 4 contributors.

### Negative / Trade-offs
- If a third connector is added later (e.g. a different university platform), adding it requires no structural change — but if 5+ connectors were needed, the flat approach would show strain. At that point, full hexagonal or a plugin registry would be warranted.
- There is no enforced compile-time boundary preventing `sync_engine.py` from accidentally importing `google/` — this is a convention, not a language-level constraint. Code review and linting (`ruff` import order rules) enforce it.

### Neutral / Notes
- This decision is revisable without a full rewrite. If the project grows beyond 3 connectors, migrating to hexagonal is a mechanical refactor, not a design change.
