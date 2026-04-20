## MODIFIED Requirements

### Requirement: OAuth browser consent on first run
After storage mode is determined, the daemon SHALL open the Google OAuth consent URL in the student's default browser, requesting the scopes `https://www.googleapis.com/auth/calendar.events` and `https://www.googleapis.com/auth/calendar.readonly`. If the browser cannot be opened, the daemon SHALL print the URL and wait for the student to paste the authorisation code.

#### Scenario: Browser opens successfully
- **WHEN** the OAuth flow starts and a default browser is available
- **THEN** the browser opens the Google consent screen automatically

#### Scenario: Headless / no browser available
- **WHEN** the OAuth flow starts and no browser can be opened (e.g. SSH session)
- **THEN** the daemon prints: `Open this URL in your browser: <url>` and waits for the student to paste the auth code

---

### Requirement: Scope mismatch triggers re-authorisation
If an existing `token.json` does not include all required scopes (e.g., `calendar.readonly` is missing because the token was issued before this change), the daemon SHALL discard the token and trigger a fresh OAuth consent flow.

#### Scenario: Token missing calendar.readonly scope
- **WHEN** daemon starts and `token.json` exists but does not include `https://www.googleapis.com/auth/calendar.readonly`
- **THEN** the daemon prints: `Re-authorisation required (new permissions needed). Opening browser...` and starts a fresh OAuth flow

#### Scenario: Token has all required scopes
- **WHEN** daemon starts and `token.json` exists with both `calendar.events` and `calendar.readonly` scopes
- **THEN** no re-authorisation is triggered and the daemon proceeds normally
