"""Tests for cronwarden.watchdog and cronwarden.cli_watchdog."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from cronwarden.models import CronJob
from cronwarden.parser import parse_cron_line
from cronwarden.snapshotter import Snapshot
from cronwarden.watchdog import StaleJob, WatchdogReport, check_stale
from cronwarden.cli_watchdog import add_watchdog_subcommand


def _make_job(cmd: str = "backup.sh", server: str = "web1") -> CronJob:
    expr = parse_cron_line("0 2 * * *")
    return CronJob(schedule=expr, command=cmd, server=server)


def _snapshot(jobs, taken_at: datetime) -> Snapshot:
    s = Snapshot(jobs=list(jobs), taken_at=taken_at)
    return s


# ---------------------------------------------------------------------------
# StaleJob / WatchdogReport unit tests
# ---------------------------------------------------------------------------

def test_stale_job_str():
    job = _make_job()
    ts = datetime(2024, 1, 1, 0, 0, 0)
    s = StaleJob(job=job, last_seen=ts, days_missing=10)
    assert "STALE" in str(s)
    assert "web1" in str(s)
    assert "10d" in str(s)


def test_report_no_stale_has_no_issues():
    r = WatchdogReport()
    assert not r.has_stale
    assert "all jobs are current" in r.summary()


def test_report_with_stale_has_issues():
    job = _make_job()
    ts = datetime(2024, 1, 1)
    r = WatchdogReport(stale=[StaleJob(job=job, last_seen=ts, days_missing=8)])
    assert r.has_stale
    assert "1 stale" in r.summary()


def test_report_str_includes_stale_entries():
    job = _make_job()
    ts = datetime(2024, 1, 1)
    r = WatchdogReport(stale=[StaleJob(job=job, last_seen=ts, days_missing=8)])
    text = str(r)
    assert "STALE" in text
    assert "backup.sh" in text


# ---------------------------------------------------------------------------
# check_stale logic
# ---------------------------------------------------------------------------

def test_no_stale_when_all_jobs_present():
    job = _make_job()
    now = datetime.utcnow()
    baseline = _snapshot([job], taken_at=now - timedelta(days=30))
    current = _snapshot([job], taken_at=now)
    report = check_stale(current, baseline, threshold_days=7)
    assert not report.has_stale


def test_stale_detected_when_job_missing_beyond_threshold():
    job = _make_job()
    now = datetime.utcnow()
    old_ts = now - timedelta(days=10)
    baseline = _snapshot([job], taken_at=old_ts)
    current = _snapshot([], taken_at=now)  # job gone
    report = check_stale(current, baseline, threshold_days=7)
    assert report.has_stale
    assert report.stale[0].job.command == "backup.sh"


def test_not_stale_if_missing_within_threshold():
    job = _make_job()
    now = datetime.utcnow()
    recent_ts = now - timedelta(days=3)
    baseline = _snapshot([job], taken_at=recent_ts)
    current = _snapshot([], taken_at=now)
    report = check_stale(current, baseline, threshold_days=7)
    # baseline is only 3 days old — within threshold
    assert not report.has_stale


# ---------------------------------------------------------------------------
# CLI sub-command registration
# ---------------------------------------------------------------------------

def test_add_watchdog_subcommand_registers():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_watchdog_subcommand(sub)
    args = parser.parse_args(["watchdog", "snap.json", "crontab.txt"])
    assert hasattr(args, "func")
    assert args.threshold == 7
