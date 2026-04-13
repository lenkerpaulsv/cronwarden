"""Tests for cronwarden.linter and cronwarden.cli_lint."""

from __future__ import annotations

import argparse
from unittest.mock import patch

import pytest

from cronwarden.linter import LintWarning, lint_job, lint_jobs
from cronwarden.models import CronJob
from cronwarden.parser import parse_cron_line
from cronwarden.cli_lint import add_lint_subcommand, _run_lint


def _make_job(schedule: str, command: str = "echo hi", server: str = "srv1") -> CronJob:
    line = f"{schedule} {command}"
    return parse_cron_line(line, server=server)


# --- lint_job unit tests ---

def test_every_minute_triggers_w001():
    job = _make_job("* * * * *")
    warnings = lint_job(job)
    codes = [w.code for w in warnings]
    assert "W001" in codes


def test_specific_schedule_no_w001():
    job = _make_job("0 3 * * *")
    warnings = lint_job(job)
    codes = [w.code for w in warnings]
    assert "W001" not in codes


def test_empty_command_triggers_w002():
    job = _make_job("0 3 * * *", command="")
    # Force empty command after construction
    job.command = ""
    warnings = lint_job(job)
    codes = [w.code for w in warnings]
    assert "W002" in codes


def test_reboot_schedule_triggers_w003():
    job = CronJob(server="srv1", schedule="@reboot", command="/usr/bin/init", raw="@reboot /usr/bin/init")
    warnings = lint_job(job)
    codes = [w.code for w in warnings]
    assert "W003" in codes


def test_normal_job_no_warnings():
    job = _make_job("15 6 * * 1")
    warnings = lint_job(job)
    assert warnings == []


# --- lint_jobs aggregate tests ---

def test_lint_jobs_aggregates_warnings():
    jobs = [
        _make_job("* * * * *", server="s1"),
        _make_job("0 2 * * *", server="s2"),
    ]
    result = lint_jobs(jobs)
    assert result.has_warnings
    assert any(w.code == "W001" for w in result.warnings)


def test_lint_jobs_no_warnings():
    jobs = [_make_job("30 4 * * *", server="s1")]
    result = lint_jobs(jobs)
    assert not result.has_warnings
    assert result.summary() == "No lint warnings found."


def test_lint_result_summary_count():
    jobs = [
        _make_job("* * * * *", server="s1"),
        _make_job("* * * * *", server="s2"),
    ]
    result = lint_jobs(jobs)
    assert "2" in result.summary()


# --- cli_lint tests ---

def test_add_lint_subcommand_registers():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers()
    add_lint_subcommand(subs)
    args = parser.parse_args(["lint", "--file", "some.tab"])
    assert hasattr(args, "func")


def test_run_lint_no_warnings_returns_zero(tmp_path):
    tab = tmp_path / "jobs.tab"
    tab.write_text("srv1 0 6 * * * /bin/backup\n")
    ns = argparse.Namespace(file=str(tab), dir=None, strict=False)
    code = _run_lint(ns)
    assert code == 0


def test_run_lint_strict_with_warnings_returns_one(tmp_path):
    tab = tmp_path / "jobs.tab"
    tab.write_text("srv1 * * * * * /bin/spam\n")
    ns = argparse.Namespace(file=str(tab), dir=None, strict=True)
    code = _run_lint(ns)
    assert code == 1


def test_run_lint_strict_no_warnings_returns_zero(tmp_path):
    tab = tmp_path / "jobs.tab"
    tab.write_text("srv1 0 12 * * 1 /bin/weekly\n")
    ns = argparse.Namespace(file=str(tab), dir=None, strict=True)
    code = _run_lint(ns)
    assert code == 0
