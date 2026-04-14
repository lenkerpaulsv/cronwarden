"""Baseline management: compare current cron jobs against a saved baseline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from cronwarden.models import CronJob
from cronwarden.snapshotter import Snapshot, save_snapshot, load_snapshot


@dataclass
class BaselineDiff:
    added: List[CronJob] = field(default_factory=list)
    removed: List[CronJob] = field(default_factory=list)
    unchanged: List[CronJob] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed)

    def summary(self) -> str:
        parts = []
        if self.added:
            parts.append(f"{len(self.added)} added")
        if self.removed:
            parts.append(f"{len(self.removed)} removed")
        if not parts:
            return "No changes from baseline."
        return "Baseline diff: " + ", ".join(parts) + "."

    def __str__(self) -> str:
        lines = [self.summary()]
        for job in self.added:
            lines.append(f"  + [{job.server}] {job.command}")
        for job in self.removed:
            lines.append(f"  - [{job.server}] {job.command}")
        return "\n".join(lines)


def _index(jobs: List[CronJob]) -> dict:
    return {job.identifier(): job for job in jobs}


def compare_to_baseline(current: List[CronJob], baseline: Snapshot) -> BaselineDiff:
    """Compare *current* jobs against the jobs stored in *baseline*."""
    baseline_jobs = [
        CronJob(**{k: v for k, v in entry.items() if k != "raw"})
        for entry in baseline.to_dict()["jobs"]
    ]
    current_idx = _index(current)
    baseline_idx = _index(baseline_jobs)

    added = [j for k, j in current_idx.items() if k not in baseline_idx]
    removed = [j for k, j in baseline_idx.items() if k not in current_idx]
    unchanged = [j for k, j in current_idx.items() if k in baseline_idx]

    return BaselineDiff(added=added, removed=removed, unchanged=unchanged)


def save_baseline(jobs: List[CronJob], path: str) -> Snapshot:
    """Capture a snapshot of *jobs* and persist it to *path*."""
    snap = Snapshot.capture(jobs)
    save_snapshot(snap, path)
    return snap


def load_baseline(path: str) -> Optional[Snapshot]:
    """Load a previously saved baseline snapshot from *path*."""
    return load_snapshot(path)
