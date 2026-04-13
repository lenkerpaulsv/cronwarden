"""Notification module for cronwarden — emits alerts for audit issues."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from cronwarden.models import CronAuditResult
from cronwarden.linter import LintResult
from cronwarden.conflict import ConflictResult


@dataclass
class Notification:
    level: str  # 'error' | 'warning' | 'info'
    source: str  # e.g. 'audit', 'lint', 'conflict'
    message: str

    def __str__(self) -> str:
        return f"[{self.level.upper()}] ({self.source}) {self.message}"


@dataclass
class NotificationBundle:
    notifications: List[Notification] = field(default_factory=list)

    def add(self, n: Notification) -> None:
        self.notifications.append(n)

    @property
    def errors(self) -> List[Notification]:
        return [n for n in self.notifications if n.level == "error"]

    @property
    def warnings(self) -> List[Notification]:
        return [n for n in self.notifications if n.level == "warning"]

    def is_empty(self) -> bool:
        return len(self.notifications) == 0

    def summary(self) -> str:
        e = len(self.errors)
        w = len(self.warnings)
        return f"{e} error(s), {w} warning(s)"


def notify_from_audit(result: CronAuditResult) -> NotificationBundle:
    """Build notifications from a CronAuditResult."""
    bundle = NotificationBundle()
    for job in result.invalid_jobs:
        bundle.add(Notification(
            level="error",
            source="audit",
            message=f"Invalid cron job '{job.identifier}' on '{job.server}': {job.raw_line}",
        ))
    return bundle


def notify_from_lint(result: LintResult) -> NotificationBundle:
    """Build notifications from a LintResult."""
    bundle = NotificationBundle()
    for w in result.warnings:
        bundle.add(Notification(
            level="warning",
            source="lint",
            message=str(w),
        ))
    return bundle


def notify_from_conflicts(conflicts: List[ConflictResult]) -> NotificationBundle:
    """Build notifications from detected conflicts."""
    bundle = NotificationBundle()
    for c in conflicts:
        bundle.add(Notification(
            level="warning",
            source="conflict",
            message=str(c),
        ))
    return bundle


def merge_bundles(*bundles: NotificationBundle) -> NotificationBundle:
    """Merge multiple NotificationBundles into one."""
    merged = NotificationBundle()
    for b in bundles:
        for n in b.notifications:
            merged.add(n)
    return merged
