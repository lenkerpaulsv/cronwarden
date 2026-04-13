"""Group cron jobs by various attributes for analysis and reporting."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from cronwarden.models import CronJob


class JobGroup:
    """A named collection of cron jobs sharing a common attribute."""

    def __init__(self, key: str, jobs: List[CronJob]) -> None:
        self.key = key
        self.jobs = list(jobs)

    def __len__(self) -> int:
        return len(self.jobs)

    def __repr__(self) -> str:
        return f"JobGroup(key={self.key!r}, count={len(self.jobs)})"

    def __str__(self) -> str:
        lines = [f"Group '{self.key}' ({len(self.jobs)} job(s):"]
        for job in self.jobs:
            lines.append(f"  [{job.server}] {job.schedule} {job.command}")
        return "\n".join(lines)


class GroupIndex:
    """Index of job groups keyed by a grouping strategy."""

    def __init__(self, groups: Dict[str, JobGroup]) -> None:
        self._groups = groups

    def keys(self) -> List[str]:
        return sorted(self._groups.keys())

    def get(self, key: str) -> JobGroup:
        return self._groups[key]

    def __len__(self) -> int:
        return len(self._groups)

    def summary(self) -> str:
        lines = [f"GroupIndex: {len(self._groups)} group(s)"]
        for key in self.keys():
            lines.append(f"  {key}: {len(self._groups[key])} job(s)")
        return "\n".join(lines)


def group_by_server(jobs: List[CronJob]) -> GroupIndex:
    """Group jobs by their server name."""
    buckets: Dict[str, List[CronJob]] = defaultdict(list)
    for job in jobs:
        buckets[job.server].append(job)
    return GroupIndex({k: JobGroup(k, v) for k, v in buckets.items()})


def group_by_schedule(jobs: List[CronJob]) -> GroupIndex:
    """Group jobs that share an identical schedule expression."""
    buckets: Dict[str, List[CronJob]] = defaultdict(list)
    for job in jobs:
        buckets[job.schedule].append(job)
    return GroupIndex({k: JobGroup(k, v) for k, v in buckets.items()})


def group_by_command_prefix(jobs: List[CronJob], prefix_words: int = 1) -> GroupIndex:
    """Group jobs by the first N words of their command string."""
    buckets: Dict[str, List[CronJob]] = defaultdict(list)
    for job in jobs:
        words = job.command.split()
        key = " ".join(words[:prefix_words]) if words else "(empty)"
        buckets[key].append(job)
    return GroupIndex({k: JobGroup(k, v) for k, v in buckets.items()})
