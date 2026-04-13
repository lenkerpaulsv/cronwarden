"""Validates cron jobs for common issues beyond basic parsing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from cronwarden.models import CronJob


@dataclass
class ValidationIssue:
    job_id: str
    code: str
    message: str

    def __str__(self) -> str:
        return f"[{self.code}] {self.job_id}: {self.message}"


@dataclass
class ValidationReport:
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return len(self.issues) > 0

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.code.startswith("E"))

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.code.startswith("W"))

    def summary(self) -> str:
        if not self.has_issues:
            return "All jobs passed validation."
        return (
            f"{len(self.issues)} issue(s) found: "
            f"{self.error_count} error(s), {self.warning_count} warning(s)."
        )

    def issues_for(self, job_id: str) -> List[ValidationIssue]:
        return [i for i in self.issues if i.job_id == job_id]


def _check_duplicate_ids(jobs: List[CronJob], report: ValidationReport) -> None:
    seen: dict[str, int] = {}
    for job in jobs:
        jid = job.identifier
        seen[jid] = seen.get(jid, 0) + 1
    for jid, count in seen.items():
        if count > 1:
            report.issues.append(
                ValidationIssue(
                    job_id=jid,
                    code="E001",
                    message=f"Duplicate job identifier appears {count} times.",
                )
            )


def _check_missing_command(jobs: List[CronJob], report: ValidationReport) -> None:
    for job in jobs:
        if not job.command or not job.command.strip():
            report.issues.append(
                ValidationIssue(
                    job_id=job.identifier,
                    code="E002",
                    message="Job has an empty or missing command.",
                )
            )


def _check_invalid_expressions(jobs: List[CronJob], report: ValidationReport) -> None:
    for job in jobs:
        if not job.is_valid:
            report.issues.append(
                ValidationIssue(
                    job_id=job.identifier,
                    code="E003",
                    message=f"Invalid cron expression: '{job.raw_schedule}'.",
                )
            )


def validate_jobs(jobs: List[CronJob]) -> ValidationReport:
    """Run all validation checks against a list of CronJob instances."""
    report = ValidationReport()
    _check_invalid_expressions(jobs, report)
    _check_missing_command(jobs, report)
    _check_duplicate_ids(jobs, report)
    return report
