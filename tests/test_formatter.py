"""Tests for cronwarden.formatter.describe_schedule."""

import pytest
from cronwarden.parser import parse_cron_line
from cronwarden.formatter import describe_schedule


def get_expr(line: str):
    job = parse_cron_line(line, server="test")
    return job.expression


def test_every_minute():
    expr = get_expr("* * * * * /bin/task")
    assert describe_schedule(expr) == "every minute"


def test_specific_minute_and_hour():
    expr = get_expr("30 6 * * * /bin/task")
    result = describe_schedule(expr)
    assert "30" in result
    assert "6" in result


def test_step_minutes():
    expr = get_expr("*/15 * * * * /bin/task")
    result = describe_schedule(expr)
    assert "every 15 minutes" in result


def test_specific_day_of_month():
    expr = get_expr("0 9 1 * * /bin/task")
    result = describe_schedule(expr)
    assert "day-of-month 1" in result


def test_specific_month():
    expr = get_expr("0 0 * 6 * /bin/task")
    result = describe_schedule(expr)
    assert "June" in result


def test_specific_day_of_week():
    expr = get_expr("0 8 * * 1 /bin/task")
    result = describe_schedule(expr)
    assert "Monday" in result


def test_range_field():
    expr = get_expr("0 9-17 * * * /bin/task")
    result = describe_schedule(expr)
    assert "9" in result
    assert "17" in result


def test_list_field():
    expr = get_expr("0 0 * * 1,3,5 /bin/task")
    result = describe_schedule(expr)
    assert "Monday" in result
    assert "Wednesday" in result
    assert "Friday" in result


def test_full_schedule_description_is_string():
    expr = get_expr("*/5 */2 15 12 0 /bin/task")
    result = describe_schedule(expr)
    assert isinstance(result, str)
    assert len(result) > 0
    assert "December" in result
    assert "Sunday" in result
