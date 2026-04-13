"""Tests for cronwarden.writer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cronwarden.models import CronAuditResult, CronJob
from cronwarden.parser import parse_cron_line
from cronwarden.reporter import AuditReport
from cronwarden.writer import _infer_format, write_report


def _make_report() -> AuditReport:
    expr = parse_cron_line("0 * * * *")
    job = CronJob(server="s1", command="cmd", raw_line="0 * * * *", expression=expr)
    result = CronAuditResult(valid_jobs=[job], invalid_jobs=[], conflicts=[])
    return AuditReport(result)


def test_infer_format_from_extension():
    assert _infer_format(Path("out.json"), None) == "json"
    assert _infer_format(Path("out.csv"), None) == "csv"
    assert _infer_format(Path("out.md"), None) == "markdown"
    assert _infer_format(Path("out.markdown"), None) == "markdown"


def test_infer_format_explicit_overrides_extension():
    assert _infer_format(Path("out.csv"), "json") == "json"


def test_infer_format_unknown_extension_raises():
    with pytest.raises(ValueError, match="Cannot infer export format"):
        _infer_format(Path("out.txt"), None)


def test_write_report_to_json_file(tmp_path: Path):
    report = _make_report()
    out = tmp_path / "report.json"
    write_report(report, "json", str(out))
    data = json.loads(out.read_text())
    assert "summary" in data


def test_write_report_to_csv_file(tmp_path: Path):
    report = _make_report()
    out = tmp_path / "report.csv"
    write_report(report, "csv", str(out))
    content = out.read_text()
    assert content.startswith("server,command")


def test_write_report_to_markdown_file(tmp_path: Path):
    report = _make_report()
    out = tmp_path / "report.md"
    write_report(report, "markdown", str(out))
    content = out.read_text()
    assert "# CronWarden Audit Report" in content


def test_write_report_creates_parent_dirs(tmp_path: Path):
    report = _make_report()
    out = tmp_path / "nested" / "deep" / "report.json"
    write_report(report, "json", str(out))
    assert out.exists()


def test_write_report_stdout(capsys):
    report = _make_report()
    write_report(report, "csv", output_path=None)
    captured = capsys.readouterr()
    assert "server,command" in captured.out
