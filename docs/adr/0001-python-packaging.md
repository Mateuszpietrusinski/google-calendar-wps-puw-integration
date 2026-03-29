# ADR-0001: Clone-and-Run with Python Setup Script

**Date:** 2026-03-29
**Status:** Proposed
**Deciders:** Architect, Team
**Related ADRs:** ADR-0003 (token storage)

---

## Context

The original proposal was `pipx install ahe-sync` from PyPI. This was rejected for two reasons:

1. **Security:** Publishing a package to PyPI creates a permanent public artifact. Even if the package contains no secrets at the time of publishing, any accidental inclusion of a token file, `.env`, or cached credential in a future build would expose student data publicly and irreversibly.
2. **Data locality:** The tool's design principle is that no data is transmitted to the project team. A PyPI package model works against this principle — it centralises distribution in a way that invites future mistakes (bundled secrets, telemetry, auto-update channels).

The PRD target user (CS student) is comfortable cloning a GitHub repo. The ≤ 30-minute setup target remains achievable without PyPI.

## Decision

We will distribute `ahe-sync` **exclusively via GitHub clone**. A Python cross-platform setup script at `scripts/setup.py` handles the full first-time setup.

**Student workflow:**
```
git clone https://github.com/<org>/ahe-sync
cd ahe-sync
python scripts/setup.py
# → edit .env with credentials
# → python -m ahe_sync
```

`scripts/setup.py` does exactly four things:
1. Creates a local virtualenv at `.venv/` (using `venv` from stdlib — no external deps)
2. Installs dependencies into it from `pyproject.toml` (`pip install -e .` inside the venv)
3. Copies `.env.example` → `.env` if no `.env` exists yet
4. Prints next steps: edit `.env`, then run the daemon

The daemon is started with:
- **macOS/Linux:** `.venv/bin/python -m ahe_sync`
- **Windows:** `.venv\Scripts\python -m ahe_sync`

`scripts/setup.py` also prints the correct start command for the student's OS at the end.

## Consequences

### Positive
- **No public package = no risk of accidentally publishing sensitive data.** The entire security surface is the student's own machine and their private fork.
- The setup script uses only Python stdlib (`venv`, `subprocess`, `shutil`, `sys`, `pathlib`) — no bootstrapping dependencies.
- Cross-platform: works on Windows, macOS, and Linux with `python scripts/setup.py`.
- Students work directly from source; `git pull` is the update mechanism.
- Future contributors see the full source immediately after clone.

### Negative / Trade-offs
- Students must have Python 3.10+ installed before running the setup script. This must be documented as a prerequisite in the README with OS-specific install links.
- No version pinning via PyPI — students always get the HEAD of the branch they cloned. Versioning via git tags is recommended.
- No `pipx`-style global command — students must be in the project directory or use the full path to start the daemon.

### Neutral / Notes
- `.gitignore` must include `.venv/`, `.env`, `token.json`, `state.json`, and `*.pyc`.
- A `requirements.txt` pinned lockfile alongside `pyproject.toml` is recommended for reproducible installs.
- If the team decides to publish to PyPI in a future version, this ADR should be revisited and a secrets-audit step added to the release process.
