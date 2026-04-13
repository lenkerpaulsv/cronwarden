"""Tests for cronwarden.validator."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from cronwarden.models import CronJob
from cronwarden.validator import (
    ValidationIssue,
    ValidationReport,
    validate_jobs,
)


def _make_job(
    server: str = "srv1",
    command: str = "echo hi",
    raw_schedule: str = "* * * * *",
    is_valid: bool = True,
) -> CronJob:
    job = MagicMock(spec=CronJob)
    job.server = server
    job.command = command
    job.raw_schedule = raw_schedule
    job.is_valid = is_valid
    job.identifier = f"{server}:{raw_schedule}:{command}"
    return job


# --- ValidationIssue ---

def test_validation_issue_str():
    issue = ValidationIssue(job_id="srv:* * * * *:cmd", code="E001", message="Dup.")
    assert "E001" in str(issue)
    assert "Dup." in str(issue)


# --- ValidationReport ---

def test_report_empty_has_no_issues():
    report = ValidationReport()
    assert not report.has_issues
    assert report.error_count == 0
    assert report.warning_count == 0


def test_report_summary_no_issues():
    report = ValidationReport()
    assert "passed" in report.summary()


def test_report_summary_with_issues():
    report = ValidationReport(
        issues=[
            ValidationIssue("id", "E001", "error"),
            ValidationIssue("id", "W001", "warning"),
        ]
    )
    assert "2 issue(s)" in report.summary()
    assert "1 error" in report.summary()
    assert "1 warning" in report.summary()


def test_report_issues_for_filters_by_id():
    report = ValidationReport(
        issues=[
            ValidationIssue("job_a", "E001", "msg"),
            ValidationIssue("job_b", "E002", "msg"),
        ]
    )
    assert len(report.issues_for("job_a")) == 1
    assert len(report.issues_for("job_b")) == 1
    assert len(report.issues_for("job_c")) == 0


# --- validate_jobs ---

def test_valid_jobs_produce_no_issues():
    jobs = [_make_job(), _make_job(server="srv2", command="backup")]
    report = validate_jobs(jobs)
    assert not report.has_issues


def test_invalid_expression_triggers_e003():
    job = _make_job(raw_schedule="bad expr", is_valid=False)
    report = validate_jobs([job])
    codes = [i.code for i in report.issues]
    assert "E003" in codes


def test_empty_command_triggers_e002():
    job = _make_job(command="  ")
    report = validate_jobs([job])
    codes = [i.code for i in report.issues]
    assert "E002" in codes


def test_duplicate_ids_trigger_e001():
    job1 = _make_job()
    job2 = _make_job()  # same identifier by construction
    report = validate_jobs([job1, job2])
    codes = [i.code for i in report.issues]
    assert "E001" in codes


def test_multiple_errors_accumulate():
    job = _make_job(command="", raw_schedule="??", is_valid=False)
    report = validate_jobs([job])
    assert report.error_count >= 2
