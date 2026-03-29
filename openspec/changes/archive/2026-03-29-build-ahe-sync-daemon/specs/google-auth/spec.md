## ADDED Requirements

### Requirement: First-run consent prompt before writing token to disk
On first start, if no token exists in memory or on disk and `TOKEN_STORAGE` is not set in `.env`, the daemon SHALL display a plain-language prompt asking the student to choose between local storage (default) and memory-only mode before any OAuth flow begins.

#### Scenario: Prompt shown on first run with no TOKEN_STORAGE set
- **WHEN** the daemon starts and no token is found and `TOKEN_STORAGE` is absent from `.env`
- **THEN** the daemon prints the storage choice prompt with options `[1] local (default)` and `[2] memory only` before opening any browser

#### Scenario: Student accepts default by pressing Enter
- **WHEN** the student presses Enter without typing a choice
- **THEN** `local` mode is selected, token is written to `~/.config/ahe-sync/token.json` with permissions `600`, and `prefs.json` records the choice

#### Scenario: Student explicitly chooses memory mode
- **WHEN** the student enters `2` at the prompt
- **THEN** no token file is written to disk, token is held in process memory only, and `prefs.json` records the choice

#### Scenario: Prompt is not repeated on subsequent starts
- **WHEN** `prefs.json` exists with a recorded choice
- **THEN** the daemon uses that choice without displaying the prompt again

---

### Requirement: TOKEN_STORAGE env var bypasses prompt
If `TOKEN_STORAGE` is set in `.env`, the daemon SHALL use that mode directly without prompting.

#### Scenario: TOKEN_STORAGE=local skips prompt
- **WHEN** `TOKEN_STORAGE=local` is set and no token file exists
- **THEN** daemon proceeds directly to OAuth flow and stores token to disk after consent

#### Scenario: TOKEN_STORAGE=memory skips prompt
- **WHEN** `TOKEN_STORAGE=memory` is set
- **THEN** daemon proceeds directly to OAuth flow and holds token in memory only

---

### Requirement: OAuth browser consent on first run
After storage mode is determined, the daemon SHALL open the Google OAuth consent URL in the student's default browser. If the browser cannot be opened, the daemon SHALL print the URL and wait for the student to paste the authorisation code.

#### Scenario: Browser opens successfully
- **WHEN** the OAuth flow starts and a default browser is available
- **THEN** the browser opens the Google consent screen automatically

#### Scenario: Headless / no browser available
- **WHEN** the OAuth flow starts and no browser can be opened (e.g. SSH session)
- **THEN** the daemon prints: `Open this URL in your browser: <url>` and waits for the student to paste the auth code

---

### Requirement: Token reuse across daemon restarts (local mode)
When `TOKEN_STORAGE=local` and `token.json` exists, the daemon SHALL load the token from disk on startup without triggering a new consent flow. If the access token is expired, it SHALL be refreshed silently using the stored refresh token.

#### Scenario: Valid token loaded on restart
- **WHEN** daemon starts and `token.json` exists with a valid refresh token
- **THEN** no browser is opened and the daemon proceeds directly to the scheduler

#### Scenario: Expired access token refreshed silently
- **WHEN** daemon starts and `token.json` contains an expired access token but a valid refresh token
- **THEN** a new access token is obtained silently and `token.json` is updated

---

### Requirement: Re-authorisation on every restart (memory mode)
When `TOKEN_STORAGE=memory`, the daemon SHALL trigger the OAuth browser consent flow automatically on every start since no token is persisted between runs.

#### Scenario: Browser opens on every restart in memory mode
- **WHEN** the daemon starts with `TOKEN_STORAGE=memory`
- **THEN** the OAuth browser flow is triggered regardless of any previous session
