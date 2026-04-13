"""Tests for cronwarden parser and loader modules."""

import tempfile
import os
import pytest

from cronwarden.parser import parse_cron_line, CronExpression
from cronwarden.loader import load_crontab_file


# --- Parser tests ---

def test_parse_valid_simple():
    expr = parse_cron_line("0 5 * * 1 /usr/bin/backup.sh")
    assert expr is not None
    assert expr.is_valid is True
    assert expr.minute == "0"
    assert expr.hour == "5"
    assert expr.command == "/usr/bin/backup.sh"


def test_parse_valid_with_range_and_step():
    expr = parse_cron_line("*/15 0-6 1,15 * * /opt/run.sh --quiet")
    assert expr is not None
    assert expr.is_valid is True
    assert expr.command == "/opt/run.sh --quiet"


def test_parse_month_alias():
    expr = parse_cron_line("0 0 1 Jan * /bin/monthly")
    assert expr is not None
    assert expr.is_valid is True
    assert expr.month == "1"


def test_parse_dow_alias():
    expr = parse_cron_line("0 9 * * Mon /bin/weekly")
    assert expr is not None
    assert expr.is_valid is True
    assert expr.day_of_week == "1"


def test_parse_invalid_minute_out_of_range():
    expr = parse_cron_line("99 5 * * * /bin/bad")
    assert expr is not None
    assert expr.is_valid is False
    assert "minute" in expr.error


def test_parse_invalid_hour():
    expr = parse_cron_line("0 25 * * * /bin/bad")
    assert expr is not None
    assert expr.is_valid is False
    assert "hour" in expr.error


def test_parse_too_few_fields():
    expr = parse_cron_line("0 5 * *")
    assert expr is not None
    assert expr.is_valid is False


def test_parse_comment_returns_none():
    assert parse_cron_line("# this is a comment") is None


def test_parse_blank_line_returns_none():
    assert parse_cron_line("   ") is None


# --- Loader tests ---

def _write_crontab(lines):
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".crontab", delete=False)
    tmp.write("\n".join(lines))
    tmp.close()
    return tmp.name


def test_load_valid_crontab():
    path = _write_crontab([
        "# daily backup",
        "0 2 * * * /usr/bin/backup",
        "*/5 * * * * /usr/bin/healthcheck",
    ])
    try:
        result = load_crontab_file(path, server="server1")
        assert result.total == 2
        assert len(result.valid_jobs) == 2
        assert len(result.invalid_jobs) == 0
    finally:
        os.unlink(path)


def test_load_crontab_with_invalid_entry():
    path = _write_crontab([
        "0 2 * * * /usr/bin/backup",
        "99 99 * * * /usr/bin/bad",
    ])
    try:
        result = load_crontab_file(path, server="server2")
        assert result.total == 2
        assert len(result.invalid_jobs) == 1
    finally:
        os.unlink(path)


def test_load_nonexistent_file():
    result = load_crontab_file("/nonexistent/path/crontab", server="ghost")
    assert result.total == 0
    assert len(result.parse_errors) == 1
    assert "not found" in result.parse_errors[0].lower()


def test_load_macro_syntax_reported_as_error():
    path = _write_crontab(["@reboot /usr/bin/start"])
    try:
        result = load_crontab_file(path, server="server3")
        assert len(result.parse_errors) == 1
        assert "Macro" in result.parse_errors[0]
    finally:
        os.unlink(path)
