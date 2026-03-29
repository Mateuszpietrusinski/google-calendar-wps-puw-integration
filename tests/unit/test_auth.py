"""Unit tests for ahe_sync/google/auth.py."""

import json
import os
import stat
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _make_config(token_storage: str = "") -> MagicMock:
    cfg = MagicMock()
    cfg.token_storage = token_storage
    cfg.google_client_id = "test-id"
    cfg.google_client_secret = "test-secret"
    return cfg


def _make_creds(valid=True, expired=False, refresh_token="rtoken"):
    creds = MagicMock()
    creds.valid = valid
    creds.expired = expired
    creds.refresh_token = refresh_token
    creds.to_json.return_value = '{"token": "fake"}'
    return creds


# ── memory mode ──────────────────────────────────────────────────────────────

def test_memory_mode_never_writes_to_disk(tmp_path):
    from ahe_sync.google import auth as auth_module

    fake_creds = _make_creds()
    with (
        patch.object(auth_module, "_CONFIG_DIR", tmp_path),
        patch.object(auth_module, "_TOKEN_PATH", tmp_path / "token.json"),
        patch.object(auth_module, "_PREFS_PATH", tmp_path / "prefs.json"),
        patch.object(auth_module, "_run_oauth_flow", return_value=fake_creds),
    ):
        result = auth_module.get_valid_credentials(_make_config(token_storage="memory"))

    assert not (tmp_path / "token.json").exists()
    assert result is fake_creds


# ── local mode ───────────────────────────────────────────────────────────────

def test_local_mode_writes_token_json(tmp_path):
    from ahe_sync.google import auth as auth_module

    fake_creds = _make_creds()
    with (
        patch.object(auth_module, "_CONFIG_DIR", tmp_path),
        patch.object(auth_module, "_TOKEN_PATH", tmp_path / "token.json"),
        patch.object(auth_module, "_PREFS_PATH", tmp_path / "prefs.json"),
        patch.object(auth_module, "_load_token", return_value=None),
        patch.object(auth_module, "_run_oauth_flow", return_value=fake_creds),
    ):
        result = auth_module.get_valid_credentials(_make_config(token_storage="local"))

    assert (tmp_path / "token.json").exists()


def test_local_mode_reuses_valid_token(tmp_path):
    from ahe_sync.google import auth as auth_module

    valid_creds = _make_creds(valid=True, expired=False)
    with (
        patch.object(auth_module, "_CONFIG_DIR", tmp_path),
        patch.object(auth_module, "_TOKEN_PATH", tmp_path / "token.json"),
        patch.object(auth_module, "_PREFS_PATH", tmp_path / "prefs.json"),
        patch.object(auth_module, "_load_token", return_value=valid_creds),
        patch.object(auth_module, "_run_oauth_flow") as mock_flow,
    ):
        result = auth_module.get_valid_credentials(_make_config(token_storage="local"))

    mock_flow.assert_not_called()
    assert result is valid_creds


def test_local_mode_refreshes_expired_token(tmp_path):
    from ahe_sync.google import auth as auth_module

    expired_creds = _make_creds(valid=False, expired=True, refresh_token="rtoken")
    with (
        patch.object(auth_module, "_CONFIG_DIR", tmp_path),
        patch.object(auth_module, "_TOKEN_PATH", tmp_path / "token.json"),
        patch.object(auth_module, "_PREFS_PATH", tmp_path / "prefs.json"),
        patch.object(auth_module, "_load_token", return_value=expired_creds),
        patch.object(auth_module, "_save_token"),
        patch("google.auth.transport.requests.Request"),
    ):
        result = auth_module.get_valid_credentials(_make_config(token_storage="local"))

    expired_creds.refresh.assert_called_once()


# ── prompt (TOKEN_STORAGE not set) ───────────────────────────────────────────

def test_prompt_default_enter_selects_local(tmp_path, monkeypatch):
    from ahe_sync.google import auth as auth_module

    fake_creds = _make_creds()
    monkeypatch.setattr("builtins.input", lambda _: "")  # Enter = default
    with (
        patch.object(auth_module, "_CONFIG_DIR", tmp_path),
        patch.object(auth_module, "_TOKEN_PATH", tmp_path / "token.json"),
        patch.object(auth_module, "_PREFS_PATH", tmp_path / "prefs.json"),
        patch.object(auth_module, "_load_token", return_value=None),
        patch.object(auth_module, "_run_oauth_flow", return_value=fake_creds),
    ):
        auth_module.get_valid_credentials(_make_config(token_storage=""))

    prefs = json.loads((tmp_path / "prefs.json").read_text())
    assert prefs["token_storage"] == "local"


def test_prompt_choice_2_selects_memory(tmp_path, monkeypatch):
    from ahe_sync.google import auth as auth_module

    fake_creds = _make_creds()
    monkeypatch.setattr("builtins.input", lambda _: "2")
    with (
        patch.object(auth_module, "_CONFIG_DIR", tmp_path),
        patch.object(auth_module, "_TOKEN_PATH", tmp_path / "token.json"),
        patch.object(auth_module, "_PREFS_PATH", tmp_path / "prefs.json"),
        patch.object(auth_module, "_run_oauth_flow", return_value=fake_creds),
    ):
        auth_module.get_valid_credentials(_make_config(token_storage=""))

    assert not (tmp_path / "token.json").exists()
    prefs = json.loads((tmp_path / "prefs.json").read_text())
    assert prefs["token_storage"] == "memory"


def test_env_var_bypasses_prompt(tmp_path):
    """TOKEN_STORAGE=memory should never call the prompt."""
    from ahe_sync.google import auth as auth_module

    fake_creds = _make_creds()
    with (
        patch.object(auth_module, "_CONFIG_DIR", tmp_path),
        patch.object(auth_module, "_TOKEN_PATH", tmp_path / "token.json"),
        patch.object(auth_module, "_PREFS_PATH", tmp_path / "prefs.json"),
        patch.object(auth_module, "_prompt_storage_choice") as mock_prompt,
        patch.object(auth_module, "_run_oauth_flow", return_value=fake_creds),
    ):
        auth_module.get_valid_credentials(_make_config(token_storage="memory"))

    mock_prompt.assert_not_called()
