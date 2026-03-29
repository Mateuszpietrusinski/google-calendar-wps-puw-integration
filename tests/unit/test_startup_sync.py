"""Unit tests for _run_startup_syncs() in ahe_sync/__main__.py."""

from unittest.mock import MagicMock, call
from ahe_sync.__main__ import _run_startup_syncs


def test_both_jobs_called_when_both_enabled():
    puw_job = MagicMock()
    wps_job = MagicMock()

    _run_startup_syncs(puw_job, wps_job)

    puw_job.assert_called_once()
    wps_job.assert_called_once()


def test_only_puw_called_when_wps_disabled():
    puw_job = MagicMock()

    _run_startup_syncs(puw_job, None)

    puw_job.assert_called_once()


def test_only_wps_called_when_puw_disabled():
    wps_job = MagicMock()

    _run_startup_syncs(None, wps_job)

    wps_job.assert_called_once()


def test_puw_failure_does_not_prevent_wps_job():
    puw_job = MagicMock(side_effect=RuntimeError("AuthError: PUW login failed"))
    wps_job = MagicMock()

    # Should not raise
    _run_startup_syncs(puw_job, wps_job)

    puw_job.assert_called_once()
    wps_job.assert_called_once()
