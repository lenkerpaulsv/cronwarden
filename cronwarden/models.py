"""Data models for cronwarden cron job entries."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class CronJob:
    """Represents a single cron job entry from a server."""
    server: str
    user: str
    schedule: str
    command: str
    source_file: str
    line_number: int
    is_valid: bool = True
    validation_error: Optional[str] = None

    @property
    def identifier(self) -> str:
        """Unique identifier for deduplication and conflict detection."""
        return f"{self.server}:{self.user}:{self.schedule}:{self.command}"

    def __str__(self) -> str:
        status = "OK" if self.is_valid else f"INVALID({self.validation_error})"
        return f"[{self.server}] {self.user}: {self.schedule} {self.command} [{status}]"


@dataclass
class CronAuditResult:
    """Aggregated result of auditing cron jobs across servers."""
    server: str
    source_file: str
    jobs: List[CronJob] = field(default_factory=list)
    parse_errors: List[str] = field(default_factory=list)

    @property
    def valid_jobs(self) -> List[CronJob]:
        return [j for j in self.jobs if j.is_valid]

    @property
    def invalid_jobs(self) -> List[CronJob]:
        return [j for j in self.jobs if not j.is_valid]

    @property
    def total(self) -> int:
        return len(self.jobs)

    def summary(self) -> str:
        return (
            f"Server: {self.server} | File: {self.source_file} | "
            f"Total: {self.total} | Valid: {len(self.valid_jobs)} | "
            f"Invalid: {len(self.invalid_jobs)} | ParseErrors: {len(self.parse_errors)}"
        )
