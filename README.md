# ahe-sync

Sync AHE university platform events into Google Calendar automatically.

Connects **PUW** (Moodle e-learning, `platforma.ahe.lodz.pl`) and **WPS** (zjazd timetable, `wpsapi.ahe.lodz.pl`) to your personal Google Calendar. Runs as a local daemon on your machine — nothing is sent to the project team.

---

## Prerequisites

- **Python 3.10 or newer** installed and available as `python3`
  - macOS: `brew install python@3.13` or download from python.org
  - Windows: download from python.org (tick "Add to PATH" during install)
  - Linux: `sudo apt install python3.10` (or your distro's equivalent)
- A **Google account** (the calendar you want events added to)
- Your **AHE PUW username + password** (your Moodle login)
- Your **AHE WPS username + password** (your WPS login) — optional if you only want PUW sync

---

## Setup

**1. Clone the repository**

```bash
git clone https://github.com/<org>/ahe-sync
cd ahe-sync
```

**2. Run the setup script**

```bash
python3 scripts/setup.py
```

This creates a `.venv/` with all dependencies and copies `.env.example` to `.env`.

**3. Edit `.env` with your credentials**

```bash
nano .env       # macOS / Linux
notepad .env    # Windows
```

Fill in at minimum:

```dotenv
GOOGLE_CLIENT_ID=<from the team — see Discord>
GOOGLE_CLIENT_SECRET=<from the team — see Discord>

PUW_USERNAME=your_puw_login
PUW_PASSWORD=your_puw_password

WPS_USERNAME=your_wps_login
WPS_PASSWORD=your_wps_password
```

Omit `PUW_USERNAME`/`PUW_PASSWORD` entirely to disable PUW sync.
Omit `WPS_USERNAME`/`WPS_PASSWORD` entirely to disable WPS sync.

> **Security warning:** `.env` contains your passwords in plaintext.
> Never commit it to version control.
> Restrict file permissions: `chmod 600 .env` (macOS/Linux).

**4. Start the daemon**

macOS / Linux:
```bash
.venv/bin/python -m ahe_sync
```

Windows:
```
.venv\Scripts\python -m ahe_sync
```

---

## First run — Google OAuth

On first start, the daemon asks where to store your Google OAuth token:

```
  [1] Stored locally on this machine (~/.config/ahe-sync/token.json)  <- default
      -> Convenient: daemon restarts without re-authorisation.
      -> Token is written to disk (chmod 600). Never share this file.

  [2] Kept in memory only (this session)
      -> Nothing written to disk.
      -> You will need to re-authorise every time the daemon restarts.

Choose [1/2], or press Enter for default [1]:
```

Press **Enter** to accept the default (local storage). Your browser opens for Google consent. After you grant access, the daemon starts syncing immediately.

If you chose option `[2]` (memory), the browser opens automatically each time the daemon restarts.

> **Security note:** If you chose local storage, your token is saved at
> `~/.config/ahe-sync/token.json` with permissions `chmod 600`.
> Never share or commit this file.

---

## Sync schedule

| Source | Schedule |
|--------|----------|
| PUW | Every 10 minutes |
| WPS | 12:00 and 21:00 CET (Europe/Warsaw) |

The daemon logs each sync run to the terminal:

```
[2026-04-01 12:00:01 CET] [DAEMON] Started. PUW: every 10 min | WPS: 12:00, 21:00 CET
[2026-04-01 12:00:02 CET] [PUW] ✓ 2 created, 0 updated, 1 deleted
[2026-04-01 12:00:02 CET] [WPS] ✓ 0 created, 3 updated, 0 deleted
```

---

## Stopping the daemon

Press **CTRL+C**. The daemon finishes any in-progress sync and exits cleanly:

```
[2026-04-01 14:37:55 CET] [DAEMON] Stopped.
```

---

## Removing synced events

To remove all **future** ahe-sync events from Google Calendar without touching past events or personal events:

macOS / Linux:
```bash
.venv/bin/python -m ahe_sync remove --source puw
.venv/bin/python -m ahe_sync remove --source wps
```

Windows:
```
.venv\Scripts\python -m ahe_sync remove --source puw
.venv\Scripts\python -m ahe_sync remove --source wps
```

---

## Resetting / uninstalling

```bash
# 1. Remove future synced events (optional but recommended)
.venv/bin/python -m ahe_sync remove --source puw
.venv/bin/python -m ahe_sync remove --source wps

# 2. Delete local state, token, and preferences
rm -rf ~/.config/ahe-sync/

# 3. Delete the repository
cd ..
rm -rf ahe-sync/
```

---

## Configuration reference

All settings live in `.env`. See `.env.example` for the full list with descriptions.

| Key | Required | Default | Description |
|-----|----------|---------|-------------|
| `GOOGLE_CLIENT_ID` | Yes | — | OAuth Client ID (from team) |
| `GOOGLE_CLIENT_SECRET` | Yes | — | OAuth Client Secret (from team) |
| `PUW_USERNAME` / `PUW_PASSWORD` | No | — | Omit both to disable PUW sync |
| `WPS_USERNAME` / `WPS_PASSWORD` | No | — | Omit both to disable WPS sync |
| `TOKEN_STORAGE` | No | prompt | `local` (persist to disk) or `memory` (in-process only) |
| `GOOGLE_CALENDAR_ID` | No | `primary` | Target calendar ID |
| `PUW_POLL_INTERVAL_MINUTES` | No | `10` | Minimum enforced: 10 |
| `WPS_POLL_TIMES_CET` | No | `12:00,21:00` | Comma-separated HH:MM in Europe/Warsaw |

---

## Troubleshooting

**`AuthError: PUW login failed`** — check `PUW_USERNAME` and `PUW_PASSWORD` in `.env`.

**`AuthError: WPS login failed`** — check `WPS_USERNAME` and `WPS_PASSWORD` in `.env`.

**`Error: Missing required .env fields`** — the daemon exits on startup if required fields are missing. Edit `.env` and add the listed values.

**Browser does not open for OAuth** — the daemon prints a URL. Copy it into your browser manually and paste the authorisation code back into the terminal.

**Re-run the OAuth consent flow** — delete `~/.config/ahe-sync/token.json` and `~/.config/ahe-sync/prefs.json`, then restart the daemon.
