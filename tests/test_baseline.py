"""Tests for cronwarden.baseline and cronwarden.cli_baseline."""

from __future__ import annotations

import json
import os
from argparse import Namespace
from unittest.mock import patch, MagicMock

import pytest

from cronwarden.models import CronJob
from cronwarden.parser import parse_cron_line
from cronwarden.snapshotter import Snapshot
from cronwarden.baseline import compare_to_baseline, save_baseline, load_baseline, BaselineDiff
from cronwarden.cli_baseline import add_baseline_subcommand, _run_baseline


def _make_job(server: str, command: str, schedule: str = "0 * * * *") -> CronJob:
    expr = parse_cron_line(schedule)
    return CronJob(server=server, command=command, schedule=schedule, expression=expr, raw=schedule)


# ---------------------------------------------------------------------------
# BaselineDiff unit tests
# ---------------------------------------------------------------------------

def test_no_changes_empty_diff():
    diff = BaselineDiff()
    assert not diff.has_changes
    assert "No changes" in diff.summary()


def test_has_changes_when_added():
    job = _make_job("web", "backup.sh")
    diff = BaselineDiff(added=[job])
    assert diff.has_changes
    assert "1 added" in diff.summary()


def test_has_changes_when_removed():
    job = _make_job("web", "cleanup.sh")
    diff = BaselineDiff(removed=[job])
    assert diff.has_changes
    assert "1 removed" in diff.summary()


def test_str_contains_plus_and_minus():
    added = _make_job("a", "new.sh")
    removed = _make_job("b", "old.sh")
    diff = BaselineDiff(added=[added], removed=[removed])
    text = str(diff)
    assert "+ [a]" in text
    assert "- [b]" in text


# ---------------------------------------------------------------------------
# compare_to_baseline
# ---------------------------------------------------------------------------

def test_identical_jobs_no_changes():
    jobs = [_make_job("srv", "run.sh")]
    snap = Snapshot.capture(jobs)
    diff = compare_to_baseline(jobs, snap)
    assert not diff.has_changes
    assert len(diff.unchanged) == 1


def test_added_job_detected():
    original = [_make_job("srv", "run.sh")]
    snap = Snapshot.capture(original)
    current = original + [_make_job("srv", "extra.sh")]
    diff = compare_to_baseline(current, snap)
    assert len(diff.added) == 1
    assert diff.added[0].command == "extra.sh"


def test_removed_job_detected():
    original = [_make_job("srv", "run.sh"), _make_job("srv", "old.sh")]
    snap = Snapshot.capture(original)
    current = [_make_job("srv", "run.sh")]
    diff = compare_to_baseline(current, snap)
    assert len(diff.removed) == 1
    assert diff.removed[0].command == "old.sh"


# ---------------------------------------------------------------------------
# save_baseline / load_baseline (filesystem)
# ---------------------------------------------------------------------------

def test_save_and_load_baseline(tmp_path):
    jobs = [_make_job("host", "sync.sh")]
    path = str(tmp_path / "baseline.json")
    snap = save_baseline(jobs, path)
    assert os.path.exists(path)
    loaded = load_baseline(path)
    assert loaded is not None
    assert len(loaded.jobs) == 1


def test_load_baseline_missing_file_returns_none(tmp_path):
    result = load_baseline(str(tmp_path / "nonexistent.json"))
    assert result is None


# ---------------------------------------------------------------------------
# CLI sub-command
# ---------------------------------------------------------------------------

def test_add_baseline_subcommand_registers():
    import argparse
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()
    add_baseline_subcommand(sub)
    args = p.parse_args(["baseline", "some/path", "--save"])
    assert args.func is not None


def test_run_baseline_save(tmp_path):
    jobs = [_make_job("s", "cmd.sh")]
    bf = str(tmp_path / "bl.json")
    ns = Namespace(path="irrelevant", baseline_file=bf, save=True, compare=False, func=None)
    with patch("cronwarden.cli_baseline._load", return_value=jobs):
        rc = _run_baseline(ns)
    assert rc == 0
    assert os.path.exists(bf)


def test_run_baseline_compare_no_changes(tmp_path):
    jobs = [_make_job("s", "cmd.sh")]
    bf = str(tmp_path / "bl.json")
    save_baseline(jobs, bf)
    ns = Namespace(path="irrelevant", baseline_file=bf, save=False, compare=True, func=None)
    with patch("cronwarden.cli_baseline._load", return_value=jobs):
        rc = _run_baseline(ns)
    assert rc == 0


def test_run_baseline_compare_missing_baseline(tmp_path):
    bf = str(tmp_path / "missing.json")
    ns = Namespace(path="irrelevant", baseline_file=bf, save=False, compare=True, func=None)
    with patch("cronwarden.cli_baseline._load", return_value=[]):
        rc = _run_baseline(ns)
    assert rc == 2
