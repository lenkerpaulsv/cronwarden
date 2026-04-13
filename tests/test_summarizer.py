"""Tests for cronwarden.summarizer."""
from __future__ import annotations

import pytest

from cronwarden.models import CronJob
from cronwarden.parser import parse_cron_line
from cronwarden.summarizer import build_summary, CronSummary, ServerSummary


def _make_job(schedule: str, command: str, server: str) -> CronJob:
    expr = parse_cron_line(schedule)
    return CronJob(schedule=schedule, command=command, server=server, expression=expr)


def _make_invalid_job(command: str, server: str) -> CronJob:
    return CronJob(schedule="bad", command=command, server=server, expression=None)


# ---------------------------------------------------------------------------
# ServerSummary
# ---------------------------------------------------------------------------

def test_server_summary_valid_jobs():
    ss = ServerSummary(server="web", total_jobs=5, invalid_jobs=2)
    assert ss.valid_jobs == 3


def test_server_summary_str():
    ss = ServerSummary(server="web", total_jobs=4, invalid_jobs=1)
    text = str(ss)
    assert "web" in text
    assert "total=4" in text
    assert "valid=3" in text
    assert "invalid=1" in text


# ---------------------------------------------------------------------------
# build_summary
# ---------------------------------------------------------------------------

def test_build_summary_empty():
    summary = build_summary([])
    assert isinstance(summary, CronSummary)
    assert summary.total_jobs == 0
    assert len(summary.servers) == 0


def test_build_summary_single_server():
    jobs = [
        _make_job("* * * * *", "cmd1", "host-a"),
        _make_job("0 * * * *", "cmd2", "host-a"),
    ]
    summary = build_summary(jobs)
    assert len(summary.servers) == 1
    assert "host-a" in summary.servers
    ss = summary.servers["host-a"]
    assert ss.total_jobs == 2
    assert ss.invalid_jobs == 0
    assert ss.valid_jobs == 2


def test_build_summary_multiple_servers():
    jobs = [
        _make_job("* * * * *", "cmd1", "host-a"),
        _make_job("0 0 * * *", "cmd2", "host-b"),
        _make_job("5 4 * * *", "cmd3", "host-b"),
    ]
    summary = build_summary(jobs)
    assert summary.total_jobs == 3
    assert len(summary.servers) == 2
    assert summary.servers["host-b"].total_jobs == 2


def test_build_summary_counts_invalid():
    jobs = [
        _make_job("0 0 * * *", "good", "host-a"),
        _make_invalid_job("bad", "host-a"),
    ]
    summary = build_summary(jobs)
    ss = summary.servers["host-a"]
    assert ss.total_jobs == 2
    assert ss.invalid_jobs == 1
    assert ss.valid_jobs == 1
    assert summary.total_invalid == 1
    assert summary.total_valid == 1


def test_build_summary_commands_recorded():
    jobs = [
        _make_job("* * * * *", "/usr/bin/backup", "host-a"),
        _make_job("0 0 * * *", "/usr/bin/clean", "host-a"),
    ]
    summary = build_summary(jobs)
    cmds = summary.servers["host-a"].commands
    assert "/usr/bin/backup" in cmds
    assert "/usr/bin/clean" in cmds


def test_cron_summary_str_contains_server():
    jobs = [_make_job("* * * * *", "cmd", "srv-1")]
    summary = build_summary(jobs)
    text = str(summary)
    assert "srv-1" in text
    assert "1 server(s)" in text


def test_server_names_sorted():
    jobs = [
        _make_job("* * * * *", "c", "zebra"),
        _make_job("* * * * *", "c", "alpha"),
        _make_job("* * * * *", "c", "mango"),
    ]
    summary = build_summary(jobs)
    assert summary.server_names() == ["alpha", "mango", "zebra"]
