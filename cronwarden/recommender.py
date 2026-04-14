"""Schedule recommendation engine for cronwarden.

Analyzes existing cron jobs and suggests optimizations or alternatives
based on common patterns, resource contention, and best practices.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from cronwarden.models import CronJob


@dataclass
class Recommendation:
    job_id: str
    code: str
    message: str
    suggested_schedule: str | None = None

    def __str__(self) -> str:
        base = f"[{self.code}] {self.job_id}: {self.message}"
        if self.suggested_schedule:
            base += f" (suggested: '{self.suggested_schedule}')"
        return base


@dataclass
class RecommendationReport:
    recommendations: List[Recommendation] = field(default_factory=list)

    def has_recommendations(self) -> bool:
        return len(self.recommendations) > 0

    def summary(self) -> str:
        n = len(self.recommendations)
        return f"{n} recommendation{'s' if n != 1 else ''} generated."

    def by_code(self, code: str) -> List[Recommendation]:
        return [r for r in self.recommendations if r.code == code]


def _is_top_of_hour_pile(jobs: List[CronJob]) -> List[CronJob]:
    """Return jobs scheduled at minute 0 (top-of-hour) that could be staggered."""
    result = []
    for job in jobs:
        if not job.is_valid:
            continue
        expr = job.expression
        if expr and expr.minute == "0" and expr.hour != "*":
            result.append(job)
    return result


def _is_every_minute(job: CronJob) -> bool:
    if not job.is_valid or job.expression is None:
        return False
    e = job.expression
    return e.minute == "*" and e.hour == "*"


def build_recommendations(jobs: List[CronJob]) -> RecommendationReport:
    report = RecommendationReport()

    # R001: Jobs running every minute — suggest a less frequent interval
    for job in jobs:
        if _is_every_minute(job):
            report.recommendations.append(
                Recommendation(
                    job_id=job.identifier,
                    code="R001",
                    message="Job runs every minute; consider a less frequent schedule.",
                    suggested_schedule="*/5 * * * *",
                )
            )

    # R002: Multiple jobs piling up at the top of the hour on the same server
    top_of_hour = _is_top_of_hour_pile(jobs)
    servers: dict[str, list[CronJob]] = {}
    for job in top_of_hour:
        servers.setdefault(job.server, []).append(job)
    for server, grp in servers.items():
        if len(grp) >= 3:
            for idx, job in enumerate(grp):
                report.recommendations.append(
                    Recommendation(
                        job_id=job.identifier,
                        code="R002",
                        message=(
                            f"{len(grp)} jobs start at minute 0 on '{server}'; "
                            "stagger them to reduce load."
                        ),
                        suggested_schedule=f"{idx * 5} * * * *",
                    )
                )

    # R003: Invalid jobs — recommend fixing the schedule
    for job in jobs:
        if not job.is_valid:
            report.recommendations.append(
                Recommendation(
                    job_id=job.identifier,
                    code="R003",
                    message="Job has an invalid schedule expression; review and correct it.",
                )
            )

    return report
