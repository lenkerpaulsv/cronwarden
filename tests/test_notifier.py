"""Tests for cronwarden.notifier."""

from __future__ import annotations

import pytest

from cronwarden.models import CronJob, CronAuditResult
from cronwarden.parser import CronExpression
from cronwarden.linter import LintWarning, LintResult
from cronwarden.conflict import ConflictResult
from cronwarden.notifier import (
    Notification,
    NotificationBundle,
    notify_from_audit,
    notify_from_lint,
    notify_from_conflicts,
    merge_bundles,
)


def _make_expr() -> CronExpression:
    return CronExpression(
        minute="*", hour="*", dom="*", month="*", dow="*", raw="* * * * *"
    )


def _make_job(cmd: str = "backup.sh", server: str = "web-01") -> CronJob:
    return CronJob(
        server=server,
        schedule=_make_expr(),
        command=cmd,
        raw_line=f"* * * * * {cmd}",
    )


# --- Notification and NotificationBundle ---

def test_notification_str():
    n = Notification(level="error", source="audit", message="something broke")
    assert "ERROR" in str(n)
    assert "audit" in str(n)
    assert "something broke" in str(n)


def test_bundle_empty_initially():
    b = NotificationBundle()
    assert b.is_empty()
    assert b.errors == []
    assert b.warnings == []


def test_bundle_add_and_filter():
    b = NotificationBundle()
    b.add(Notification(level="error", source="audit", message="e1"))
    b.add(Notification(level="warning", source="lint", message="w1"))
    b.add(Notification(level="warning", source="conflict", message="w2"))
    assert len(b.errors) == 1
    assert len(b.warnings) == 2
    assert not b.is_empty()


def test_bundle_summary():
    b = NotificationBundle()
    b.add(Notification(level="error", source="audit", message="e"))
    b.add(Notification(level="warning", source="lint", message="w"))
    assert b.summary() == "1 error(s), 1 warning(s)"


# --- notify_from_audit ---

def test_notify_from_audit_invalid_jobs():
    job = _make_job()
    result = CronAuditResult(valid_jobs=[], invalid_jobs=[job], conflicts=[])
    bundle = notify_from_audit(result)
    assert len(bundle.errors) == 1
    assert "audit" in bundle.errors[0].source


def test_notify_from_audit_no_issues():
    result = CronAuditResult(valid_jobs=[_make_job()], invalid_jobs=[], conflicts=[])
    bundle = notify_from_audit(result)
    assert bundle.is_empty()


# --- notify_from_lint ---

def test_notify_from_lint_with_warnings():
    job = _make_job()
    w = LintWarning(code="W001", message="Runs every minute", job=job)
    lint_result = LintResult(warnings=[w])
    bundle = notify_from_lint(lint_result)
    assert len(bundle.warnings) == 1
    assert bundle.warnings[0].source == "lint"


def test_notify_from_lint_no_warnings():
    bundle = notify_from_lint(LintResult(warnings=[]))
    assert bundle.is_empty()


# --- notify_from_conflicts ---

def test_notify_from_conflicts():
    job_a = _make_job(cmd="a.sh")
    job_b = _make_job(cmd="b.sh")
    conflict = ConflictResult(job_a=job_a, job_b=job_b)
    bundle = notify_from_conflicts([conflict])
    assert len(bundle.warnings) == 1
    assert bundle.warnings[0].source == "conflict"


def test_notify_from_conflicts_empty():
    bundle = notify_from_conflicts([])
    assert bundle.is_empty()


# --- merge_bundles ---

def test_merge_bundles():
    b1 = NotificationBundle()
    b1.add(Notification(level="error", source="audit", message="e1"))
    b2 = NotificationBundle()
    b2.add(Notification(level="warning", source="lint", message="w1"))
    merged = merge_bundles(b1, b2)
    assert len(merged.notifications) == 2
    assert len(merged.errors) == 1
    assert len(merged.warnings) == 1
