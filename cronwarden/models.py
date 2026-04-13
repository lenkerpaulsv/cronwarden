"""Domain models for cronwarden."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from cronwarden.parser import CronExpression


@dataclass
class CronJob:
    schedule: str
    command: str
    server: str
    expression: CronExpression
    comment: str = ""
    tags: List[str] = field(default_factory=list)

    @property
    def identifier(self) -> str:
        """Unique-ish key: server + schedule + command."""
        return f"{self.server}::{self.schedule}::{self.command}"

    def __str__(self) -> str:
        return f"[{self.server}] {self.schedule} {self.command}"

    def __hash__(self) -> int:
        return hash(self.identifier)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CronJob):
            return NotImplemented
        return self.identifier == other.identifier


@dataclass
class CronAuditResult:
    job: CronJob
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def valid_jobs(self) -> bool:
        return len(self.errors) == 0

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    @property
    def is_clean(self) -> bool:
        return not self.has_errors and not self.has_warnings

    def __str__(self) -> str:
        status = "OK" if self.valid_jobs else "INVALID"
        return f"{status}: {self.job}"
