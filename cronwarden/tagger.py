"""Tag-based grouping and filtering of cron jobs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from cronwarden.models import CronJob


@dataclass
class TagIndex:
    """Maps tag names to the jobs that carry them."""

    _index: Dict[str, List[CronJob]] = field(default_factory=dict)

    def add(self, job: CronJob) -> None:
        """Register *job* under every tag found in its metadata."""
        for tag in job.tags:
            self._index.setdefault(tag, []).append(job)

    def jobs_for_tag(self, tag: str) -> List[CronJob]:
        """Return all jobs associated with *tag* (empty list if unknown)."""
        return list(self._index.get(tag, []))

    def all_tags(self) -> List[str]:
        """Return sorted list of every known tag."""
        return sorted(self._index.keys())

    def summary(self) -> Dict[str, int]:
        """Return a mapping of tag -> job count."""
        return {tag: len(jobs) for tag, jobs in sorted(self._index.items())}


def build_tag_index(jobs: List[CronJob]) -> TagIndex:
    """Build a :class:`TagIndex` from an iterable of jobs."""
    index = TagIndex()
    for job in jobs:
        index.add(job)
    return index


def filter_by_tag(jobs: List[CronJob], tag: str) -> List[CronJob]:
    """Return the subset of *jobs* that carry *tag*."""
    return [j for j in jobs if tag in j.tags]


def filter_by_tags(
    jobs: List[CronJob],
    tags: List[str],
    match_all: bool = False,
) -> List[CronJob]:
    """Filter *jobs* by multiple tags.

    Parameters
    ----------
    match_all:
        When ``True`` a job must carry **all** supplied tags.
        When ``False`` (default) a job must carry **at least one**.
    """
    tag_set = set(tags)
    if match_all:
        return [j for j in jobs if tag_set.issubset(set(j.tags))]
    return [j for j in jobs if tag_set & set(j.tags)]
