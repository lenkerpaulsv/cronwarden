"""Tests for cronwarden.grouper and cronwarden.cli_group."""

from __future__ import annotations

import argparse
from unittest.mock import patch

import pytest

from cronwarden.grouper import (
    JobGroup,
    GroupIndex,
    group_by_server,
    group_by_schedule,
    group_by_command_prefix,
)
from cronwarden.models import CronJob
from cronwarden.parser import parse_cron_line
from cronwarden.cli_group import add_group_subcommand, _run_group


def _make_job(server: str, schedule: str, command: str) -> CronJob:
    expr = parse_cron_line(schedule)
    return CronJob(server=server, schedule=schedule, command=command, expression=expr)


JOBS = [
    _make_job("web-01", "0 * * * *", "/usr/bin/backup.sh"),
    _make_job("web-01", "*/5 * * * *", "/usr/bin/health_check.sh"),
    _make_job("db-01", "0 * * * *", "/usr/bin/backup.sh"),
    _make_job("db-01", "30 2 * * *", "/usr/bin/vacuum.sh"),
]


def test_group_by_server_keys():
    index = group_by_server(JOBS)
    assert set(index.keys()) == {"web-01", "db-01"}


def test_group_by_server_counts():
    index = group_by_server(JOBS)
    assert len(index.get("web-01")) == 2
    assert len(index.get("db-01")) == 2


def test_group_by_schedule_shared_schedule():
    index = group_by_schedule(JOBS)
    # Both web-01 and db-01 have "0 * * * *"
    group = index.get("0 * * * *")
    assert len(group) == 2


def test_group_by_schedule_unique_schedule():
    index = group_by_schedule(JOBS)
    assert len(index.get("30 2 * * *")) == 1


def test_group_by_command_prefix_default():
    index = group_by_command_prefix(JOBS, prefix_words=1)
    # All commands start with /usr/bin/backup.sh, /usr/bin/health_check.sh, etc.
    assert "/usr/bin/backup.sh" in index.keys()


def test_group_by_command_prefix_two_words():
    jobs = [
        _make_job("s1", "* * * * *", "python manage.py migrate"),
        _make_job("s2", "* * * * *", "python manage.py collectstatic"),
        _make_job("s3", "* * * * *", "bash deploy.sh"),
    ]
    index = group_by_command_prefix(jobs, prefix_words=2)
    assert len(index.get("python manage.py")) == 2
    assert len(index.get("bash deploy.sh")) == 1


def test_job_group_str_contains_key():
    group = JobGroup("web-01", JOBS[:2])
    text = str(group)
    assert "web-01" in text


def test_group_index_summary():
    index = group_by_server(JOBS)
    summary = index.summary()
    assert "web-01" in summary
    assert "db-01" in summary


def test_add_group_subcommand_registers():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers()
    add_group_subcommand(subs)
    args = parser.parse_args(["group", "some/path", "--by", "schedule"])
    assert args.by == "schedule"
    assert args.path == "some/path"


def test_run_group_returns_zero():
    ns = argparse.Namespace(path="some/path", by="server", dir=False)
    with patch("cronwarden.cli_group._load", return_value=JOBS):
        result = _run_group(ns)
    assert result == 0


def test_run_group_empty_jobs():
    ns = argparse.Namespace(path="empty/path", by="server", dir=False)
    with patch("cronwarden.cli_group._load", return_value=[]):
        result = _run_group(ns)
    assert result == 0
