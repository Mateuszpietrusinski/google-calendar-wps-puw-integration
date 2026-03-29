# ADR-0003: Tiered Token Storage with Explicit Student Consent

**Date:** 2026-03-29
**Status:** Proposed
**Deciders:** Architect, Team
**Related ADRs:** ADR-0001 (packaging)

---

## Context

The original proposal stored the Google OAuth token unconditionally in `~/.config/ahe-sync/token.json`. This was challenged on two grounds:

1. **Security:** Writing OAuth credentials to disk without the student's explicit knowledge and consent is a RODO (Polish GDPR) concern and a general privacy risk. The token grants write access to the student's personal Google Calendar.
2. **Scalability:** A future deployment on a shared machine (Raspberry Pi, home server) or a multi-user setup requires a different security posture than a single-user laptop. Forcing one storage model limits flexibility.

The principle agreed for this project is: **no data is stored outside the student's session without their explicit consent.**

## Decision

Token storage uses three modes controlled by `TOKEN_STORAGE` in `.env`.

### Modes

| `TOKEN_STORAGE` value | Behaviour |
|----------------------|-----------|
| *(not set)* | First-run interactive prompt — student chooses; choice saved to `~/.config/ahe-sync/prefs.json` so not asked again |
| `local` | **Default.** Token persisted to `~/.config/ahe-sync/token.json` (chmod 600). No re-auth needed after restart. |
| `memory` | Token lives only in process memory. Daemon auto-opens browser for OAuth on every restart. |

A third mode (`keychain`) is reserved for future implementation via the `keyring` library (OS keychain: macOS Keychain, Windows Credential Manager, Linux Secret Service). Not in scope for v1.

### First-run prompt (when `TOKEN_STORAGE` not set)

```
ahe-sync needs to authorise with your Google account.
After authorisation, your OAuth token can be:

  [1] Stored locally on this machine (~/.config/ahe-sync/token.json)  ← default
      → Convenient: daemon restarts without re-authorisation.
      → Token is written to disk (chmod 600). Never share this file.

  [2] Kept in memory only (this session)
      → Nothing written to disk.
      → You will need to re-authorise every time the daemon restarts.

Choose [1/2], or press Enter for default [1]:
```

If the student chooses `[1]` (or presses Enter), the daemon:
1. Writes `~/.config/ahe-sync/token.json` with `chmod 600`.
2. Writes `~/.config/ahe-sync/prefs.json` recording the choice so the prompt is not repeated.
3. Prints: `Add TOKEN_STORAGE=local to your .env to skip this prompt on future installs.`

If the student chooses `[2]`, the daemon:
1. Keeps the token in memory only.
2. Records the choice in `~/.config/ahe-sync/prefs.json`.
3. Prints: `Token kept in memory. You will be asked to re-authorise when the daemon restarts.`

### Restart behaviour (memory mode)

When `TOKEN_STORAGE=memory` and the daemon starts with no token in memory, it automatically opens the Google OAuth consent URL in the default browser. If the browser cannot be opened (headless environment, SSH), the daemon prints the URL and waits for the student to paste the authorisation code back into the terminal.

### State file (`state.json`)

`state.json` tracks only Google Calendar event IDs and change-detection hashes — no credentials, no PII beyond what Google Calendar itself holds. It is stored unconditionally at `~/.config/ahe-sync/state.json`. This is not subject to the consent requirement above because it contains no credentials and no data that could be used to access external systems.

## Consequences

### Positive
- The default (`local`) is the most convenient path for the majority of students running the daemon on a personal laptop — no re-auth on restart.
- Students are still informed before any token is written to disk; pressing Enter accepts the default without friction.
- `memory` mode is available for privacy-conscious students and shared/server deployments without requiring extra documentation.
- The `TOKEN_STORAGE` env var makes the storage policy explicit and auditable in the `.env` file.

### Negative / Trade-offs
- `memory` mode means every daemon restart requires a browser OAuth round-trip. On a headless server this requires manual URL handling (URL printed to terminal).
- The interactive prompt adds one step to first-run setup. The README must document both paths clearly to stay within the ≤ 30-minute setup target.
- `prefs.json` introduces a second config file in `~/.config/ahe-sync/`. Its purpose must be documented in the README (`rm ~/.config/ahe-sync/prefs.json` to reset the prompt).

### Neutral / Notes
- `token.json`, when written, gets `chmod 600` on macOS/Linux. On Windows, the file is created in the user's profile directory where ACLs already restrict access to the owning user.
- The `keychain` mode (OS keychain via `keyring`) is the recommended upgrade path for v2. It provides `local`-mode convenience with OS-level secret protection and should be the default when implemented.
- `state.json` atomic writes: write to `.state.tmp`, then `os.replace()` to prevent corruption on mid-write crash.
