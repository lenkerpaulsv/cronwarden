"""Tests for cronwarden.exporter and cronwarden.writer."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from cronwarden.exporter import export, export_csv, export_json, export_markdown
from cronwarden.models import CronAuditResult, CronJob
from cronwarden.parser import parse_cron_line
from cronwarden.reporter import AuditReport


def _make_job(server: str, cmd: str, line: str = "*/5 * * * *") -> CronJob:
    expr = parse_cron_line(line)
    return CronJob(server=server, command=cmd, raw_line=line, expression=expr)


def _make_report(
    valid=None, invalid=None, conflicts=None
) -> AuditReport:
    result = CronAuditResult(
        valid_jobs=valid or [],
        invalid_jobs=invalid or [],
        conflicts=conflicts or [],
    )
    return AuditReport(result)


# ---------------------------------------------------------------------------
# JSON export
# ---------------------------------------------------------------------------

def test_export_json_is_valid_json():
    job = _make_job("web1", "backup.sh")
    report = _make_report(valid=[job])
    raw = export_json(report)
    data = json.loads(raw)
    assert "valid_jobs" in data
    assert data["valid_jobs"][0]["server"] == "web1"


def test_export_json_counts():
    job = _make_job("web1", "backup.sh")
    report = _make_report(valid=[job])
    data = json.loads(export_json(report))
    assert data["summary"]["valid"] == 1
    assert data["summary"]["invalid"] == 0


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------

def test_export_csv_has_header():
    report = _make_report()
    csv_text = export_csv(report)
    assert csv_text.startswith("server,command,schedule,valid,invalid_reason,conflicts")


def test_export_csv_valid_job_row():
    job = _make_job("db1", "pg_dump")
    report = _make_report(valid=[job])
    csv_text = export_csv(report)
    assert "db1" in csv_text
    assert "pg_dump" in csv_text
    assert "True" in csv_text


def test_export_csv_invalid_job_row():
    job = CronJob(server="db1", command="bad_job", raw_line="99 * * * *", expression=None)
    report = _make_report(invalid=[(job, "minute out of range")])
    csv_text = export_csv(report)
    assert "False" in csv_text
    assert "minute out of range" in csv_text


# ---------------------------------------------------------------------------
# Markdown export
# ---------------------------------------------------------------------------

def test_export_markdown_contains_headers():
    report = _make_report()
    md = export_markdown(report)
    assert "# CronWarden Audit Report" in md
    assert "## Valid Jobs" in md
    assert "## Conflicts" in md


def test_export_markdown_no_conflicts_message():
    report = _make_report()
    md = export_markdown(report)
    assert "No conflicts detected" in md


# ---------------------------------------------------------------------------
# Generic export dispatcher
# ---------------------------------------------------------------------------

def test_export_unsupported_format_raises():
    report = _make_report()
    with pytest.raises(ValueError, match="Unsupported export format"):
        export(report, "xml")


def test_export_dispatches_correctly():
    report = _make_report()
    assert export(report, "json") == export_json(report)
    assert export(report, "csv") == export_csv(report)
    assert export(report, "markdown") == export_markdown(report)
