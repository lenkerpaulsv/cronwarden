"""Conflict detection for cron job schedules."""

from dataclasses import dataclass, field
from typing import List, Tuple
from itertools import combinations

from cronwarden.models import CronJob
from cronwarden.parser import CronExpression


@dataclass
class ConflictResult:
    """Represents a detected scheduling conflict between two cron jobs."""
    job_a: CronJob
    job_b: CronJob
    reason: str

    def __str__(self) -> str:
        return (
            f"CONFLICT: '{self.job_a.identifier}' <-> '{self.job_b.identifier}': {self.reason}"
        )


def _field_overlaps(expr_a: CronExpression, expr_b: CronExpression, field: str) -> bool:
    """Check whether two expressions share at least one common value for a given field."""
    values_a: set = getattr(expr_a, field)
    values_b: set = getattr(expr_b, field)
    return bool(values_a & values_b)


def expressions_overlap(expr_a: CronExpression, expr_b: CronExpression) -> bool:
    """Return True if two cron expressions can fire at the same point in time."""
    for f in ("minutes", "hours", "days", "months", "weekdays"):
        if not _field_overlaps(expr_a, expr_b, f):
            return False
    return True


def detect_conflicts(jobs: List[CronJob]) -> List[ConflictResult]:
    """Detect scheduling conflicts among a list of cron jobs.

    Two jobs conflict when their schedules can fire at exactly the same time
    AND they share the same server (or one/both have no server specified).
    """
    conflicts: List[ConflictResult] = []

    valid_jobs = [j for j in jobs if j.expression is not None]

    for job_a, job_b in combinations(valid_jobs, 2):
        # Only flag conflicts on the same server (or when server is unset)
        if job_a.server and job_b.server and job_a.server != job_b.server:
            continue

        if expressions_overlap(job_a.expression, job_b.expression):
            reason = (
                f"both scheduled at '{job_a.raw_schedule}'"
                if job_a.raw_schedule == job_b.raw_schedule
                else f"overlapping schedules '{job_a.raw_schedule}' and '{job_b.raw_schedule}'"
            )
            conflicts.append(ConflictResult(job_a=job_a, job_b=job_b, reason=reason))

    return conflicts
