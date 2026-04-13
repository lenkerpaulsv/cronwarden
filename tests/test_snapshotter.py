"""Tests for cronwarden.snapshotter."""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from cronwarden.snapshotter import (
    Snapshot,
    save_snapshot,
    load_snapshot,
    diff_snapshots,
)


def _make_job(server: str, command: str, schedule: str = "0 * * * *") -> MagicMock:
    job = MagicMock()
    job.server = server
    job.command = command
    job.schedule.__str__ = lambda self: schedule
    job.identifier = f"{server}:{command}"
    return job


def test_snapshot_capture_records_taken_at():
    jobs = [_make_job("web1", "/bin/backup.sh")]
    snap = Snapshot.capture(jobs)
    assert snap.taken_at is not None
    assert "T" in snap.taken_at  # ISO format


def test_snapshot_capture_serializes_jobs():
    jobs = [
        _make_job("web1", "/bin/backup.sh", "0 2 * * *"),
        _make_job("db1", "/bin/vacuum.sh", "30 3 * * 0"),
    ]
    snap = Snapshot.capture(jobs)
    assert len(snap.jobs) == 2
    assert snap.jobs[0]["server"] == "web1"
    assert snap.jobs[1]["command"] == "/bin/vacuum.sh"
    assert snap.jobs[0]["schedule"] == "0 2 * * *"


def test_snapshot_roundtrip_via_dict():
    jobs = [_make_job("app1", "/usr/bin/sync", "*/5 * * * *")]
    snap = Snapshot.capture(jobs)
    restored = Snapshot.from_dict(snap.to_dict())
    assert restored.taken_at == snap.taken_at
    assert restored.jobs == snap.jobs


def test_save_and_load_snapshot(tmp_path: Path):
    jobs = [_make_job("srv1", "/opt/run.sh", "0 0 * * *")]
    snap = Snapshot.capture(jobs)
    dest = tmp_path / "snapshots" / "snap.json"
    save_snapshot(snap, dest)
    assert dest.exists()
    loaded = load_snapshot(dest)
    assert loaded.taken_at == snap.taken_at
    assert loaded.jobs == snap.jobs


def test_load_snapshot_missing_file_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_snapshot(tmp_path / "nonexistent.json")


def test_diff_snapshots_detects_added():
    old = Snapshot(taken_at="2024-01-01T00:00:00+00:00", jobs=[])
    new = Snapshot(
        taken_at="2024-01-02T00:00:00+00:00",
        jobs=[{"server": "web1", "command": "/bin/new.sh", "schedule": "0 1 * * *", "identifier": "web1:/bin/new.sh"}],
    )
    result = diff_snapshots(old, new)
    assert result["has_drift"] is True
    assert len(result["added"]) == 1
    assert result["removed"] == []


def test_diff_snapshots_detects_removed():
    job = {"server": "web1", "command": "/bin/old.sh", "schedule": "0 1 * * *", "identifier": "web1:/bin/old.sh"}
    old = Snapshot(taken_at="2024-01-01T00:00:00+00:00", jobs=[job])
    new = Snapshot(taken_at="2024-01-02T00:00:00+00:00", jobs=[])
    result = diff_snapshots(old, new)
    assert result["has_drift"] is True
    assert len(result["removed"]) == 1
    assert result["added"] == []


def test_diff_snapshots_detects_changed():
    old_job = {"server": "web1", "command": "/bin/task.sh", "schedule": "0 1 * * *", "identifier": "web1:/bin/task.sh"}
    new_job = {**old_job, "schedule": "0 2 * * *"}
    old = Snapshot(taken_at="2024-01-01T00:00:00+00:00", jobs=[old_job])
    new = Snapshot(taken_at="2024-01-02T00:00:00+00:00", jobs=[new_job])
    result = diff_snapshots(old, new)
    assert result["has_drift"] is True
    assert len(result["changed"]) == 1
    assert result["changed"][0]["old"]["schedule"] == "0 1 * * *"
    assert result["changed"][0]["new"]["schedule"] == "0 2 * * *"


def test_diff_snapshots_no_drift():
    job = {"server": "web1", "command": "/bin/task.sh", "schedule": "0 1 * * *", "identifier": "web1:/bin/task.sh"}
    old = Snapshot(taken_at="2024-01-01T00:00:00+00:00", jobs=[job])
    new = Snapshot(taken_at="2024-01-02T00:00:00+00:00", jobs=[job])
    result = diff_snapshots(old, new)
    assert result["has_drift"] is False
    assert result["added"] == []
    assert result["removed"] == []
    assert result["changed"] == []
