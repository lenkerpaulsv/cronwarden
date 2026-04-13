"""Diff crontab snapshots to detect added, removed, or changed jobs."""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple

from cronwarden.models import CronJob


@dataclass
class DiffResult:
    added: List[CronJob] = field(default_factory=list)
    removed: List[CronJob] = field(default_factory=list)
    changed: List[Tuple[CronJob, CronJob]] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def summary(self) -> str:
        parts = []
        if self.added:
            parts.append(f"+{len(self.added)} added")
        if self.removed:
            parts.append(f"-{len(self.removed)} removed")
        if self.changed:
            parts.append(f"~{len(self.changed)} changed")
        return ", ".join(parts) if parts else "no changes"

    def __str__(self) -> str:
        lines = []
        for job in self.added:
            lines.append(f"[ADDED]   {job.identifier()}")
        for job in self.removed:
            lines.append(f"[REMOVED] {job.identifier()}")
        for old, new in self.changed:
            lines.append(f"[CHANGED] {old.identifier()}")
            lines.append(f"          schedule: {old.schedule!r} -> {new.schedule!r}")
            if old.command != new.command:
                lines.append(f"          command:  {old.command!r} -> {new.command!r}")
        return "\n".join(lines) if lines else "No differences found."


def _index_jobs(jobs: List[CronJob]) -> Dict[str, CronJob]:
    """Index jobs by their identifier for fast lookup."""
    return {job.identifier(): job for job in jobs}


def diff_snapshots(old_jobs: List[CronJob], new_jobs: List[CronJob]) -> DiffResult:
    """Compare two lists of CronJob objects and return a DiffResult."""
    old_index = _index_jobs(old_jobs)
    new_index = _index_jobs(new_jobs)

    result = DiffResult()

    for key, new_job in new_index.items():
        if key not in old_index:
            result.added.append(new_job)
        else:
            old_job = old_index[key]
            if old_job.schedule != new_job.schedule or old_job.command != new_job.command:
                result.changed.append((old_job, new_job))

    for key, old_job in old_index.items():
        if key not in new_index:
            result.removed.append(old_job)

    return result
