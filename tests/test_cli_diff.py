"""Tests for cronwarden.cli_diff subcommand."""

import argparse
import pytest
from unittest.mock import patch, MagicMock

from cronwarden.cli_diff import add_diff_subcommand, _run_diff
from cronwarden.models import CronJob
from cronwarden.differ import DiffResult


def _make_job(cmd="/bin/task", server="srv"):
    return CronJob(schedule="* * * * *", command=cmd, server=server)


def _make_namespace(**kwargs):
    defaults = {"old": "old_path", "new": "new_path", "server": "srv", "summary": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_diff_subcommand_registers():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers()
    add_diff_subcommand(subs)
    args = parser.parse_args(["diff", "old", "new"])
    assert args.old == "old"
    assert args.new == "new"


def test_run_diff_no_changes_returns_zero(capsys):
    jobs = [_make_job()]
    with patch("cronwarden.cli_diff._load", side_effect=[jobs, jobs]):
        code = _run_diff(_make_namespace())
    assert code == 0


def test_run_diff_with_changes_returns_one(capsys):
    old_jobs = [_make_job("/a")]
    new_jobs = [_make_job("/a"), _make_job("/b")]
    with patch("cronwarden.cli_diff._load", side_effect=[old_jobs, new_jobs]):
        code = _run_diff(_make_namespace())
    assert code == 1


def test_run_diff_summary_flag(capsys):
    old_jobs = [_make_job("/a")]
    new_jobs = [_make_job("/b")]
    with patch("cronwarden.cli_diff._load", side_effect=[old_jobs, new_jobs]):
        _run_diff(_make_namespace(summary=True))
    out = capsys.readouterr().out
    # summary mode prints a compact line
    assert "added" in out or "removed" in out or "changed" in out or "no changes" in out


def test_run_diff_full_output(capsys):
    old_jobs = [_make_job("/gone")]
    new_jobs = [_make_job("/new")]
    with patch("cronwarden.cli_diff._load", side_effect=[old_jobs, new_jobs]):
        _run_diff(_make_namespace(summary=False))
    out = capsys.readouterr().out
    assert "[ADDED]" in out or "[REMOVED]" in out
