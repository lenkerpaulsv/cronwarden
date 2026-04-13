"""Tests for cronwarden.schedule_table — upcoming runs formatting."""

from datetime import datetime

from cronwarden.parser import parse_cron_line
from cronwarden.schedule_table import upcoming_runs, format_table


def _job(line: str, server: str = "srv"):
    return parse_cron_line(line, server=server)


FIXED = datetime(2024, 6, 1, 12, 0, 0)


def test_upcoming_runs_count():
    job = _job("* * * * * echo hi")
    rows = upcoming_runs([job], n=4, after=FIXED)
    assert len(rows) == 4


def test_upcoming_runs_server_and_command():
    job = _job("0 9 * * * echo morning", server="web01")
    rows = upcoming_runs([job], n=1, after=FIXED)
    assert rows[0]["server"] == "web01"
    assert "echo morning" in rows[0]["command"]


def test_upcoming_runs_multiple_jobs():
    jobs = [
        _job("* * * * * echo a", server="s1"),
        _job("0 * * * * echo b", server="s2"),
    ]
    rows = upcoming_runs(jobs, n=2, after=FIXED)
    assert len(rows) == 4  # 2 jobs × 2 runs each


def test_upcoming_runs_next_run_format():
    job = _job("30 14 * * * echo afternoon")
    rows = upcoming_runs([job], n=1, after=FIXED)
    assert rows[0]["next_run"] == "2024-06-01 14:30"


def test_format_table_contains_headers():
    job = _job("* * * * * echo hi")
    rows = upcoming_runs([job], n=1, after=FIXED)
    table = format_table(rows)
    assert "Server" in table
    assert "Next Run" in table


def test_format_table_empty():
    assert format_table([]) == "No upcoming runs."


def test_format_table_row_count():
    job = _job("* * * * * echo hi")
    rows = upcoming_runs([job], n=3, after=FIXED)
    table = format_table(rows)
    # Each data row appears between separator lines
    data_lines = [l for l in table.splitlines() if l.startswith("|") and "Server" not in l]
    assert len(data_lines) == 3
