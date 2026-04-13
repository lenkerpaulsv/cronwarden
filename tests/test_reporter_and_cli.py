"""Tests for the reporter module and CLI entry point."""

import json
import pytest
from unittest.mock import patch, MagicMock

from cronwarden.models import CronJob, CronAuditResult
from cronwarden.conflict import ConflictResult
from cronwarden.reporter import AuditReport, generate_report
from cronwarden.cli import run


def make_job(name, schedule="0 * * * *", server="srv1", command="/bin/true"):
    from cronwarden.parser import parse_cron_line
    expr, _ = parse_cron_line(schedule)
    return CronJob(name=name, schedule=schedule, command=command, server=server, expression=expr)


# --- Reporter tests ---

def test_report_summary_counts():
    valid = [make_job("job1"), make_job("job2")]
    invalid = [(make_job("badjob"), "invalid minute")]
    audit = CronAuditResult(valid_jobs=valid, invalid_jobs=invalid)
    report = AuditReport(audit_result=audit, conflicts=[])
    summary = report.summary()
    assert "Total jobs scanned : 3" in summary
    assert "Valid jobs         : 2" in summary
    assert "Invalid jobs       : 1" in summary
    assert "Conflicts detected : 0" in summary


def test_report_has_issues_with_invalid():
    invalid = [(make_job("badjob"), "bad schedule")]
    audit = CronAuditResult(valid_jobs=[], invalid_jobs=invalid)
    report = AuditReport(audit_result=audit, conflicts=[])
    assert report.has_issues is True


def test_report_no_issues():
    valid = [make_job("job1")]
    audit = CronAuditResult(valid_jobs=valid, invalid_jobs=[])
    report = AuditReport(audit_result=audit, conflicts=[])
    assert report.has_issues is False
    assert "No issues found" in report.details()


def test_report_json_structure():
    job_a = make_job("job_a", server="s1")
    job_b = make_job("job_b", server="s1")
    conflict = ConflictResult(job_a=job_a, job_b=job_b, reason="identical schedules")
    audit = CronAuditResult(valid_jobs=[job_a, job_b], invalid_jobs=[])
    report = AuditReport(audit_result=audit, conflicts=[conflict])
    data = json.loads(report.to_json())
    assert data["summary"]["total"] == 2
    assert data["summary"]["conflicts"] == 1
    assert len(data["conflicts"]) == 1
    assert data["conflicts"][0]["reason"] == "identical schedules"


def test_generate_report_writes_file(tmp_path):
    outfile = str(tmp_path / "report.txt")
    audit = CronAuditResult(valid_jobs=[make_job("j1")], invalid_jobs=[])
    content = generate_report(audit, [], output_format="text", outfile=outfile)
    assert Path(outfile).exists()
    assert "CronWarden" in Path(outfile).read_text()


# --- CLI tests ---

def test_cli_missing_path(tmp_path):
    rc = run([str(tmp_path / "nonexistent.crontab")])
    assert rc == 2


def test_cli_valid_file(tmp_path):
    cron_file = tmp_path / "jobs.crontab"
    cron_file.write_text("# comment\n0 5 * * * /usr/bin/backup\n")
    rc = run([str(cron_file), "--server", "web1"])
    assert rc == 0


def test_cli_json_output(tmp_path, capsys):
    cron_file = tmp_path / "jobs.crontab"
    cron_file.write_text("30 6 * * 1 /bin/weekly\n")
    rc = run([str(cron_file), "--format", "json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "summary" in data
    assert rc == 0


from pathlib import Path
