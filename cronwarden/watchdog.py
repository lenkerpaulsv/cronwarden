"""Watchdog module: detect cron jobs that haven't been seen recently (stale jobs)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional

from cronwarden.models import CronJob
from cronwarden.snapshotter import Snapshot


@dataclass
class StaleJob:
    job: CronJob
    last_seen: datetime
    days_missing: int

    def __str__(self) -> str:
        return (
            f"[STALE] {self.job.identifier()} — last seen {self.last_seen.date()} "
            f"({self.days_missing}d ago)"
        )


@dataclass
class WatchdogReport:
    stale: List[StaleJob] = field(default_factory=list)
    checked_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def has_stale(self) -> bool:
        return len(self.stale) > 0

    def summary(self) -> str:
        if not self.has_stale:
            return "Watchdog: all jobs are current."
        return f"Watchdog: {len(self.stale)} stale job(s) detected."

    def __str__(self) -> str:
        lines = [self.summary()]
        for s in self.stale:
            lines.append(f"  {s}")
        return "\n".join(lines)


def check_stale(
    current: Snapshot,
    baseline: Snapshot,
    threshold_days: int = 7,
) -> WatchdogReport:
    """Compare *current* snapshot against *baseline*; flag jobs missing for
    longer than *threshold_days* days."""
    report = WatchdogReport()
    now = current.taken_at
    cutoff: datetime = now - timedelta(days=threshold_days)

    current_ids = {job.identifier() for job in current.jobs}

    for job in baseline.jobs:
        jid = job.identifier()
        if jid not in current_ids:
            days_missing = (now - baseline.taken_at).days
            if baseline.taken_at <= cutoff:
                report.stale.append(
                    StaleJob(
                        job=job,
                        last_seen=baseline.taken_at,
                        days_missing=days_missing,
                    )
                )

    return report
