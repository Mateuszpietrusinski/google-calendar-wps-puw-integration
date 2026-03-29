"""Unit tests for ahe_sync/config.py."""

import os
import pytest
from unittest.mock import patch


def _env(**kwargs):
    """Minimal valid env + overrides."""
    base = {
        "GOOGLE_CLIENT_ID": "test-client-id",
        "GOOGLE_CLIENT_SECRET": "test-client-secret",
    }
    base.update(kwargs)
    return base


def test_valid_config_parses(tmp_path):
    from ahe_sync.config import Config

    with patch.dict(os.environ, _env(), clear=True):
        config = Config.load(env_path=tmp_path / "nonexistent.env")

    assert config.google_client_id == "test-client-id"
    assert config.google_calendar_id == "primary"
    assert config.puw_poll_interval_minutes == 10
    assert config.wps_poll_times == [(12, 0), (21, 0)]
    assert config.token_storage == ""


def test_missing_required_fields_exits(tmp_path, capsys):
    from ahe_sync.config import Config

    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(SystemExit) as exc_info:
            Config.load(env_path=tmp_path / "nonexistent.env")

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "GOOGLE_CLIENT_ID" in captured.out
    assert "GOOGLE_CLIENT_SECRET" in captured.out


def test_missing_one_required_field_exits(tmp_path, capsys):
    from ahe_sync.config import Config

    with patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "id"}, clear=True):
        with pytest.raises(SystemExit):
            Config.load(env_path=tmp_path / "nonexistent.env")

    captured = capsys.readouterr()
    assert "GOOGLE_CLIENT_SECRET" in captured.out
    assert "GOOGLE_CLIENT_ID" not in captured.out


def test_puw_interval_below_minimum_exits(tmp_path, capsys):
    from ahe_sync.config import Config

    with patch.dict(os.environ, _env(PUW_POLL_INTERVAL_MINUTES="5"), clear=True):
        with pytest.raises(SystemExit) as exc_info:
            Config.load(env_path=tmp_path / "nonexistent.env")

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "PUW_POLL_INTERVAL_MINUTES" in captured.out
    assert "≥ 10" in captured.out


def test_puw_interval_at_minimum_is_valid(tmp_path):
    from ahe_sync.config import Config

    with patch.dict(os.environ, _env(PUW_POLL_INTERVAL_MINUTES="10"), clear=True):
        config = Config.load(env_path=tmp_path / "nonexistent.env")

    assert config.puw_poll_interval_minutes == 10


def test_puw_disabled_when_credentials_absent(tmp_path):
    from ahe_sync.config import Config

    with patch.dict(os.environ, _env(), clear=True):
        config = Config.load(env_path=tmp_path / "nonexistent.env")

    assert not config.puw_enabled


def test_puw_enabled_when_credentials_present(tmp_path):
    from ahe_sync.config import Config

    with patch.dict(os.environ, _env(PUW_USERNAME="user", PUW_PASSWORD="pass"), clear=True):
        config = Config.load(env_path=tmp_path / "nonexistent.env")

    assert config.puw_enabled


def test_wps_disabled_when_credentials_absent(tmp_path):
    from ahe_sync.config import Config

    with patch.dict(os.environ, _env(), clear=True):
        config = Config.load(env_path=tmp_path / "nonexistent.env")

    assert not config.wps_enabled


def test_invalid_token_storage_exits(tmp_path, capsys):
    from ahe_sync.config import Config

    with patch.dict(os.environ, _env(TOKEN_STORAGE="invalid"), clear=True):
        with pytest.raises(SystemExit):
            Config.load(env_path=tmp_path / "nonexistent.env")

    captured = capsys.readouterr()
    assert "TOKEN_STORAGE" in captured.out


def test_custom_wps_poll_times(tmp_path):
    from ahe_sync.config import Config

    with patch.dict(os.environ, _env(WPS_POLL_TIMES_CET="08:00,20:00"), clear=True):
        config = Config.load(env_path=tmp_path / "nonexistent.env")

    assert config.wps_poll_times == [(8, 0), (20, 0)]
