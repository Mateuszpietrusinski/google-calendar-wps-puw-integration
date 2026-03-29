"""Google OAuth 2.0 flow with tiered token storage.

Storage modes (TOKEN_STORAGE in .env):
  local  — token persisted to ~/.config/ahe-sync/token.json (chmod 600)
  memory — token held in process memory only; browser re-auth on every restart
  ""     — interactive prompt on first run; choice saved to prefs.json

On restart in memory mode, the browser is opened automatically.
If no browser is available (headless), the URL is printed and the auth
code is read from stdin.
"""

from __future__ import annotations

import json
import os
import stat
import sys
import webbrowser
from pathlib import Path
from typing import TYPE_CHECKING

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

if TYPE_CHECKING:
    from ..config import Config

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
_CONFIG_DIR = Path.home() / ".config" / "ahe-sync"
_TOKEN_PATH = _CONFIG_DIR / "token.json"
_PREFS_PATH = _CONFIG_DIR / "prefs.json"


def _ensure_config_dir() -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def _load_prefs() -> dict:
    if _PREFS_PATH.exists():
        with open(_PREFS_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_prefs(prefs: dict) -> None:
    _ensure_config_dir()
    with open(_PREFS_PATH, "w", encoding="utf-8") as f:
        json.dump(prefs, f, indent=2)


def _prompt_storage_choice() -> str:
    """Ask the student where to store the OAuth token. Returns 'local' or 'memory'."""
    print()
    print("ahe-sync needs to authorise with your Google account.")
    print("After authorisation, your OAuth token can be:")
    print()
    print("  [1] Stored locally on this machine (~/.config/ahe-sync/token.json)  <- default")
    print("      -> Convenient: daemon restarts without re-authorisation.")
    print("      -> Token is written to disk (chmod 600). Never share this file.")
    print()
    print("  [2] Kept in memory only (this session)")
    print("      -> Nothing written to disk.")
    print("      -> You will need to re-authorise every time the daemon restarts.")
    print()
    choice = input("Choose [1/2], or press Enter for default [1]: ").strip()
    if choice == "2":
        print("Token kept in memory. You will be asked to re-authorise when the daemon restarts.")
        return "memory"
    print("Token will be stored locally at ~/.config/ahe-sync/token.json")
    print("Tip: Add TOKEN_STORAGE=local to your .env to skip this prompt on future installs.")
    return "local"


def _run_oauth_flow(config: "Config") -> Credentials:
    """Run the OAuth browser consent flow and return credentials."""
    client_config = {
        "installed": {
            "client_id": config.google_client_id,
            "client_secret": config.google_client_secret,
            "redirect_uris": ["http://localhost"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }
    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    try:
        creds = flow.run_local_server(port=0, open_browser=True)
    except Exception:
        # Headless fallback: print URL, read code from stdin
        auth_url, _ = flow.authorization_url(prompt="consent")
        print(f"\nOpen this URL in your browser:\n{auth_url}\n")
        code = input("Paste the authorisation code here: ").strip()
        flow.fetch_token(code=code)
        creds = flow.credentials
    return creds


def _save_token(creds: Credentials) -> None:
    _ensure_config_dir()
    with open(_TOKEN_PATH, "w", encoding="utf-8") as f:
        f.write(creds.to_json())
    # chmod 600 — owner read/write only (no-op on Windows but harmless)
    try:
        os.chmod(_TOKEN_PATH, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass


def _load_token() -> Credentials | None:
    if not _TOKEN_PATH.exists():
        return None
    return Credentials.from_authorized_user_file(str(_TOKEN_PATH), SCOPES)


def get_valid_credentials(config: "Config") -> Credentials:
    """Return valid Google credentials, running the OAuth flow if needed.

    Respects TOKEN_STORAGE from config:
      - "local":  load from token.json; refresh silently if expired; save back
      - "memory": always run the OAuth flow (no disk read/write)
      - "":       check prefs.json for a saved choice; prompt if not found
    """
    storage_mode = config.token_storage  # "local" | "memory" | ""

    # Resolve mode from prefs if not explicitly set
    if not storage_mode:
        prefs = _load_prefs()
        storage_mode = prefs.get("token_storage", "")

    if not storage_mode:
        storage_mode = _prompt_storage_choice()
        _save_prefs({"token_storage": storage_mode})

    if storage_mode == "local":
        creds = _load_token()
        if creds and creds.valid:
            return creds
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            _save_token(creds)
            return creds
        # No valid token — run fresh OAuth flow
        creds = _run_oauth_flow(config)
        _save_token(creds)
        return creds

    # memory mode: always run OAuth flow, never touch disk
    return _run_oauth_flow(config)
