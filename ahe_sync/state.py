"""Local sync state persistence.

Stores which source events have been synced to Google Calendar, keyed by
source_id, alongside the gcal_event_id and change-detection value.

State file: ~/.config/ahe-sync/state.json
Writes are atomic via os.replace() on a .state.tmp file.

Schema:
{
  "puw": { "<source_id>": { "gcal_event_id": "...", "timemodified": 1712345678 } },
  "wps": { "<source_id>": { "gcal_event_id": "...", "checksum": "abc123" } }
}
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def _config_dir() -> Path:
    return Path.home() / ".config" / "ahe-sync"


class StateStore:
    def __init__(self, state_path: Path | None = None) -> None:
        self._path = state_path or (_config_dir() / "state.json")
        self._tmp = self._path.with_suffix(".tmp")

    def _ensure_dir(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def load(self, source: str) -> dict[str, Any]:
        """Return the state dict for a given source, or {} if not found."""
        if not self._path.exists():
            return {}
        with open(self._path, encoding="utf-8") as f:
            data = json.load(f)
        return data.get(source, {})

    def save(self, source: str, source_state: dict[str, Any]) -> None:
        """Atomically merge source_state into the full state file."""
        self._ensure_dir()
        # Load existing full state
        if self._path.exists():
            with open(self._path, encoding="utf-8") as f:
                full_state = json.load(f)
        else:
            full_state = {}

        full_state[source] = source_state

        # Atomic write: write to .tmp then os.replace()
        with open(self._tmp, "w", encoding="utf-8") as f:
            json.dump(full_state, f, indent=2)
        os.replace(self._tmp, self._path)

    def clear_source(self, source: str) -> None:
        """Remove all entries for a source (used by remove command)."""
        if not self._path.exists():
            return
        with open(self._path, encoding="utf-8") as f:
            full_state = json.load(f)
        full_state.pop(source, None)
        self._ensure_dir()
        with open(self._tmp, "w", encoding="utf-8") as f:
            json.dump(full_state, f, indent=2)
        os.replace(self._tmp, self._path)
