"""Summarizer: produce a concise per-server breakdown of cron jobs."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List

from cronwarden.models import CronJob


@dataclass
class ServerSummary:
    server: str
    total_jobs: int = 0
    invalid_jobs: int = 0
    commands: List[str] = field(default_factory=list)

    @property
    def valid_jobs(self) -> int:
        return self.total_jobs - self.invalid_jobs

    def __str__(self) -> str:
        return (
            f"[{self.server}] total={self.total_jobs} "
            f"valid={self.valid_jobs} invalid={self.invalid_jobs}"
        )


@dataclass
class CronSummary:
    servers: Dict[str, ServerSummary] = field(default_factory=dict)

    @property
    def total_jobs(self) -> int:
        return sum(s.total_jobs for s in self.servers.values())

    @property
    def total_invalid(self) -> int:
        return sum(s.invalid_jobs for s in self.servers.values())

    @property
    def total_valid(self) -> int:
        return self.total_jobs - self.total_invalid

    def server_names(self) -> List[str]:
        return sorted(self.servers.keys())

    def __str__(self) -> str:
        lines = [f"CronSummary: {len(self.servers)} server(s), {self.total_jobs} job(s)"]
        for name in self.server_names():
            lines.append(f"  {self.servers[name]}")
        return "\n".join(lines)


def build_summary(jobs: List[CronJob]) -> CronSummary:
    """Build a CronSummary from a flat list of CronJob objects."""
    buckets: Dict[str, List[CronJob]] = defaultdict(list)
    for job in jobs:
        buckets[job.server].append(job)

    summary = CronSummary()
    for server, server_jobs in buckets.items():
        ss = ServerSummary(server=server)
        for job in server_jobs:
            ss.total_jobs += 1
            if job.expression is None:
                ss.invalid_jobs += 1
            ss.commands.append(job.command)
        summary.servers[server] = ss
    return summary
