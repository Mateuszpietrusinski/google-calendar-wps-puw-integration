# PRD Template

**A lightweight PRD format optimised for Architect + Product collaboration.**

---

## Template

```markdown
# PRD: <Feature or Product Name>

**Version:** 0.1  
**Date:** YYYY-MM-DD  
**Author(s):** <Product Manager, Architect>  
**Status:** Draft | In Review | Approved

---

## 1. Problem Statement

<!-- What problem are we solving? Who experiences it and how often?
     One paragraph. No solution language yet. -->

## 2. Target Users

<!-- Who are the primary users of this feature?
     Include a brief description of their context and goals. -->

| User Type | Description |
|-----------|-------------|
| Primary   | |
| Secondary | |

## 3. Goals

<!-- What does success look like? Use measurable outcomes where possible. -->

- 
- 

## 4. Non-Goals

<!-- Explicitly state what is out of scope for this version. -->

- 
- 

## 5. MVP Scope

<!-- The minimum set of functionality that validates the core hypothesis.
     Think: what can we cut and still deliver value? -->

### In scope (MVP)
- 

### Deferred (post-MVP)
- 

## 6. User Stories / BDD Scenarios

<!-- Link to or embed key scenarios. For a PRD, a short user story format is fine.
     Detailed Gherkin scenarios live in the test/feature files. -->

- As a [user], I want to [action] so that [outcome].

## 7. Architecture Notes

<!-- High-level notes for the Architect. Diagrams, ADR candidates, integration points. -->

**Integration points:**
- 

**ADR candidates:**
- 

## 8. Open Questions

<!-- Questions that are unresolved and need answers before or during build.
     Tag each with who is responsible for answering: [PM], [Arch], [Eng] -->

| # | Question | Owner | Resolved? |
|---|----------|-------|-----------|
| 1 | | [PM] | No |
| 2 | | [Arch] | No |

## 9. Acceptance Criteria

<!-- How will we know this is done and correct?
     These should map directly to BDD scenarios or testable outcomes. -->

- [ ] 
- [ ] 

---

_This document is a living artifact. Update version and date with each revision._
```

---

## Tips for the Architect

- Use **Section 7 (Architecture Notes)** to surface ADR candidates early — don't wait until build.
- **Open Questions** is the most important section during early PRD reviews. Drive it to zero before sprint start.
- If a story in **Section 6** touches an external API (OAuth, Calendar), flag it immediately as an integration boundary requiring an adapter in the Hexagonal design.
- **MVP Scope** is a negotiation — push back on anything in "In scope" that isn't strictly necessary to validate the core value.