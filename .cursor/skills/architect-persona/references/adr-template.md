# ADR Template

**Filename convention:** `docs/adr/NNNN-short-hyphenated-title.md`  
**Status options:** `Proposed` | `Accepted` | `Deprecated` | `Superseded by ADR-NNNN`

---

## Template

```markdown
# ADR-NNNN: <Title>

**Date:** YYYY-MM-DD  
**Status:** Proposed | Accepted | Deprecated | Superseded by ADR-NNNN  
**Deciders:** <names or roles, e.g. "Architect, Tech Lead">  
**Related ADRs:** ADR-XXXX (if any)

---

## Context

<!-- What is the situation, problem, or constraint that forces this decision?
     Include relevant technical, business, or team context.
     Keep this factual — not the decision itself. -->

## Decision

<!-- What is the decision that was made?
     State it clearly and affirmatively: "We will use X because Y." -->

## Consequences

### Positive
- <!-- benefit 1 -->
- <!-- benefit 2 -->

### Negative / Trade-offs
- <!-- drawback or risk 1 -->
- <!-- drawback or risk 2 -->

### Neutral / Notes
- <!-- anything worth recording that isn't clearly positive or negative -->
```

---

## Example — Hexagonal Architecture

```markdown
# ADR-0001: Adopt Hexagonal Architecture

**Date:** 2025-06-01  
**Status:** Accepted  
**Deciders:** Architect, Tech Lead  
**Related ADRs:** —

---

## Context

The system integrates with Google Calendar API, Google OAuth 2.0, and a PostgreSQL database.
Past experience shows that tightly coupling domain logic to infrastructure makes unit testing
difficult and swapping integrations costly. We need an approach that isolates domain logic
from external concerns from day one.

## Decision

We will structure the Node.js application using Hexagonal Architecture (Ports & Adapters).
Domain logic lives in `src/domain/`, external integrations are implemented as adapters in
`src/adapters/`, and interfaces (ports) are defined in `src/ports/`.

## Consequences

### Positive
- Domain logic is fully unit-testable without infrastructure dependencies.
- Swapping or mocking external services (e.g. Calendar API) requires only a new adapter.
- Clear separation of concerns reduces cognitive load when onboarding new engineers.

### Negative / Trade-offs
- More boilerplate than a simple layered architecture.
- Engineers unfamiliar with the pattern need a brief onboarding.

### Neutral / Notes
- This decision aligns naturally with TDD — domain tests can be written before adapters exist.
```

---

## ADR Index Tip

Maintain a `docs/adr/README.md` listing all ADRs in a table:

| # | Title | Status | Date |
|---|-------|--------|------|
| 0001 | Adopt Hexagonal Architecture | Accepted | 2025-06-01 |
| 0002 | Use Google OAuth 2.0 for authentication | Accepted | 2025-06-03 |