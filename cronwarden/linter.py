"""Lint cron jobs for common issues and anti-patterns."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from cronwarden.models import CronJob
from cronwarden.parser import CronExpression


@dataclass
class LintWarning:
    job_id: str
    code: str
    message: str

    def __str__(self) -> str:
        return f"[{self.code}] {self.job_id}: {self.message}"


@dataclass
class LintResult:
    warnings: List[LintWarning] = field(default_factory=list)

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0

    def summary(self) -> str:
        if not self.has_warnings:
            return "No lint warnings found."
        return f"{len(self.warnings)} lint warning(s) found."


def _check_every_minute(job: CronJob, expr: CronExpression) -> List[LintWarning]:
    """Warn if job runs every minute (potential overload)."""
    if expr.minute == "*" and expr.hour == "*":
        return [LintWarning(job.identifier, "W001", "Job runs every minute — consider a less frequent schedule.")]
    return []


def _check_missing_command(job: CronJob) -> List[LintWarning]:
    """Warn if command is empty or whitespace only."""
    if not job.command or not job.command.strip():
        return [LintWarning(job.identifier, "W002", "Job has an empty or blank command.")]
    return []


def _check_reboot_schedule(job: CronJob) -> List[LintWarning]:
    """Warn about @reboot jobs which are hard to audit."""
    if job.schedule.strip().lower() == "@reboot":
        return [LintWarning(job.identifier, "W003", "@reboot jobs cannot be scheduled or conflict-checked.")]
    return []


def _check_broad_dow_and_dom(job: CronJob, expr: CronExpression) -> List[LintWarning]:
    """Warn when both day-of-month and day-of-week are wildcards alongside a specific hour."""
    if expr.day_of_month == "*" and expr.day_of_week == "*" and expr.hour != "*" and expr.minute != "*":
        return []
    return []


def lint_job(job: CronJob) -> List[LintWarning]:
    warnings: List[LintWarning] = []
    warnings.extend(_check_missing_command(job))
    warnings.extend(_check_reboot_schedule(job))
    if not job.parsed_expression:
        return warnings
    expr = job.parsed_expression
    warnings.extend(_check_every_minute(job, expr))
    warnings.extend(_check_broad_dow_and_dom(job, expr))
    return warnings


def lint_jobs(jobs: List[CronJob]) -> LintResult:
    all_warnings: List[LintWarning] = []
    for job in jobs:
        all_warnings.extend(lint_job(job))
    return LintResult(warnings=all_warnings)
