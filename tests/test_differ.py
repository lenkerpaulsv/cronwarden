"""Tests for cronwarden.differ module."""

import pytest
from cronwarden.models import CronJob
from cronwarden.differ import diff_snapshots, DiffResult, _index_jobs


def make_job(schedule="* * * * *", command="/bin/task", server="srv1") -> CronJob:
    return CronJob(schedule=schedule, command=command, server=server)


# --- _index_jobs ---

def test_index_jobs_keys():
    jobs = [make_job(command="/a"), make_job(command="/b")]
    idx = _index_jobs(jobs)
    assert len(idx) == 2
    for job in jobs:
        assert job.identifier() in idx


# --- diff_snapshots: no changes ---

def test_no_changes_when_identical():
    jobs = [make_job(), make_job(command="/other")]
    result = diff_snapshots(jobs, jobs[:])
    assert not result.has_changes
    assert result.summary() == "no changes"


# --- added jobs ---

def test_added_job_detected():
    old = [make_job(command="/a")]
    new = [make_job(command="/a"), make_job(command="/b")]
    result = diff_snapshots(old, new)
    assert len(result.added) == 1
    assert result.added[0].command == "/b"
    assert not result.removed
    assert not result.changed


# --- removed jobs ---

def test_removed_job_detected():
    old = [make_job(command="/a"), make_job(command="/b")]
    new = [make_job(command="/a")]
    result = diff_snapshots(old, new)
    assert len(result.removed) == 1
    assert result.removed[0].command == "/b"
    assert not result.added
    assert not result.changed


# --- changed jobs ---

def test_changed_schedule_detected():
    old = [make_job(schedule="0 * * * *", command="/a")]
    new = [make_job(schedule="5 * * * *", command="/a")]
    result = diff_snapshots(old, new)
    assert len(result.changed) == 1
    old_job, new_job = result.changed[0]
    assert old_job.schedule == "0 * * * *"
    assert new_job.schedule == "5 * * * *"


def test_changed_command_detected():
    old = [make_job(schedule="0 * * * *", command="/old")]
    new = [make_job(schedule="0 * * * *", command="/new")]
    result = diff_snapshots(old, new)
    # identifier includes command, so this is add+remove not changed
    assert len(result.added) == 1
    assert len(result.removed) == 1


# --- summary and str ---

def test_summary_string():
    result = DiffResult(
        added=[make_job(command="/x")],
        removed=[make_job(command="/y")],
        changed=[(make_job(schedule="0 1 * * *"), make_job(schedule="0 2 * * *"))],
    )
    s = result.summary()
    assert "+1" in s
    assert "-1" in s
    assert "~1" in s


def test_str_no_changes():
    result = DiffResult()
    assert "No differences" in str(result)


def test_str_with_added():
    result = DiffResult(added=[make_job(command="/new")])
    assert "[ADDED]" in str(result)


def test_str_with_removed():
    result = DiffResult(removed=[make_job(command="/old")])
    assert "[REMOVED]" in str(result)


def test_str_with_changed_shows_schedule_diff():
    old = make_job(schedule="0 1 * * *")
    new = make_job(schedule="0 2 * * *")
    result = DiffResult(changed=[(old, new)])
    text = str(result)
    assert "[CHANGED]" in text
    assert "0 1 * * *" in text
    assert "0 2 * * *" in text
