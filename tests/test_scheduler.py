"""Tests for cronwarden.scheduler — next_run calculations."""

from datetime import datetime

import pytest

from cronwarden.parser import parse_cron_line
from cronwarden.scheduler import next_run, next_run_for_job, _expand_field


def _expr(line: str):
    job = parse_cron_line(line, server="test")
    return job.expression


# ---------------------------------------------------------------------------
# _expand_field helpers
# ---------------------------------------------------------------------------

def test_expand_star():
    assert _expand_field("*", 0, 4) == [0, 1, 2, 3, 4]


def test_expand_single():
    assert _expand_field("5", 0, 59) == [5]


def test_expand_range():
    assert _expand_field("2-4", 0, 9) == [2, 3, 4]


def test_expand_step():
    assert _expand_field("*/15", 0, 59) == [0, 15, 30, 45]


def test_expand_list():
    assert _expand_field("1,3,5", 0, 9) == [1, 3, 5]


# ---------------------------------------------------------------------------
# next_run
# ---------------------------------------------------------------------------

def test_next_run_every_minute():
    expr = _expr("* * * * * echo hi")
    after = datetime(2024, 6, 1, 12, 0, 0)
    result = next_run(expr, after=after)
    assert result == datetime(2024, 6, 1, 12, 1, 0)


def test_next_run_specific_time():
    expr = _expr("30 9 * * * echo morning")
    after = datetime(2024, 6, 1, 8, 0, 0)
    result = next_run(expr, after=after)
    assert result == datetime(2024, 6, 1, 9, 30, 0)


def test_next_run_wraps_to_next_hour():
    expr = _expr("0 * * * * echo hourly")
    after = datetime(2024, 6, 1, 12, 5, 0)
    result = next_run(expr, after=after)
    assert result == datetime(2024, 6, 1, 13, 0, 0)


def test_next_run_wraps_to_next_day():
    expr = _expr("0 23 * * * echo nightly")
    after = datetime(2024, 6, 1, 23, 30, 0)
    result = next_run(expr, after=after)
    assert result == datetime(2024, 6, 2, 23, 0, 0)


def test_next_run_specific_day_of_week():
    # 1 = Monday in cron (0=Sunday)
    expr = _expr("0 9 * * 1 echo monday")
    # 2024-06-01 is a Saturday (weekday=5)
    after = datetime(2024, 6, 1, 10, 0, 0)
    result = next_run(expr, after=after)
    assert result.weekday() == 0  # Monday
    assert result.hour == 9
    assert result.minute == 0


def test_next_run_for_job():
    job = parse_cron_line("*/5 * * * * echo five", server="srv1")
    after = datetime(2024, 6, 1, 12, 3, 0)
    result = next_run_for_job(job, after=after)
    assert result == datetime(2024, 6, 1, 12, 5, 0)
