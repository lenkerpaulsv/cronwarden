"""Tests for cronwarden.conflict module."""

import pytest
from cronwarden.models import CronJob
from cronwarden.parser import parse_cron_line
from cronwarden.conflict import detect_conflicts, expressions_overlap


def make_job(schedule: str, command: str, server: str = "web01") -> CronJob:
    expr = parse_cron_line(schedule)
    return CronJob(
        raw_schedule=schedule,
        command=command,
        server=server,
        expression=expr,
    )


def test_identical_schedules_conflict():
    jobs = [
        make_job("0 * * * *", "backup.sh"),
        make_job("0 * * * *", "cleanup.sh"),
    ]
    results = detect_conflicts(jobs)
    assert len(results) == 1
    assert "backup.sh" in results[0].job_a.command or "backup.sh" in results[0].job_b.command


def test_non_overlapping_schedules_no_conflict():
    jobs = [
        make_job("0 6 * * *", "morning.sh"),
        make_job("0 18 * * *", "evening.sh"),
    ]
    results = detect_conflicts(jobs)
    assert results == []


def test_different_servers_no_conflict():
    job_a = make_job("0 * * * *", "task.sh", server="web01")
    job_b = make_job("0 * * * *", "task.sh", server="web02")
    results = detect_conflicts([job_a, job_b])
    assert results == []


def test_no_server_conflicts_with_same_server():
    job_a = make_job("30 2 * * *", "rotate.sh", server="")
    job_b = make_job("30 2 * * *", "archive.sh", server="db01")
    # empty server should not block conflict detection
    results = detect_conflicts([job_a, job_b])
    assert len(results) == 1


def test_overlapping_wildcard_and_specific():
    # "* * * * *" overlaps with any schedule
    jobs = [
        make_job("* * * * *", "heartbeat.sh"),
        make_job("15 3 * * 1", "weekly.sh"),
    ]
    results = detect_conflicts(jobs)
    assert len(results) == 1


def test_three_jobs_multiple_conflicts():
    jobs = [
        make_job("0 12 * * *", "noon_a.sh"),
        make_job("0 12 * * *", "noon_b.sh"),
        make_job("0 12 * * *", "noon_c.sh"),
    ]
    results = detect_conflicts(jobs)
    # C(3,2) = 3 pairs
    assert len(results) == 3


def test_conflict_str_representation():
    jobs = [
        make_job("0 0 * * *", "midnight_a.sh"),
        make_job("0 0 * * *", "midnight_b.sh"),
    ]
    results = detect_conflicts(jobs)
    assert len(results) == 1
    text = str(results[0])
    assert "CONFLICT" in text
    assert "midnight" in text


def test_no_jobs_returns_empty():
    assert detect_conflicts([]) == []


def test_single_job_returns_empty():
    assert detect_conflicts([make_job("*/5 * * * *", "poll.sh")]) == []
