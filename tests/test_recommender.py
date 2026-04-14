"""Tests for cronwarden.recommender and cronwarden.cli_recommend."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from cronwarden.models import CronJob
from cronwarden.parser import parse_cron_line
from cronwarden.recommender import (
    Recommendation,
    RecommendationReport,
    build_recommendations,
)


def _make_job(
    schedule: str,
    command: str = "echo hi",
    server: str = "srv1",
    tags: list[str] | None = None,
) -> CronJob:
    expr, valid = parse_cron_line(schedule)
    return CronJob(
        server=server,
        schedule=schedule,
        command=command,
        expression=expr,
        is_valid=valid,
        tags=tags or [],
    )


# ---------------------------------------------------------------------------
# Recommendation dataclass
# ---------------------------------------------------------------------------

def test_recommendation_str_no_suggestion():
    r = Recommendation(job_id="srv1:echo", code="R003", message="Bad schedule.")
    assert "R003" in str(r)
    assert "srv1:echo" in str(r)
    assert "suggested" not in str(r)


def test_recommendation_str_with_suggestion():
    r = Recommendation(
        job_id="srv1:echo",
        code="R001",
        message="Too frequent.",
        suggested_schedule="*/5 * * * *",
    )
    assert "*/5 * * * *" in str(r)


# ---------------------------------------------------------------------------
# RecommendationReport
# ---------------------------------------------------------------------------

def test_report_empty_has_no_recommendations():
    report = RecommendationReport()
    assert not report.has_recommendations()
    assert report.summary() == "0 recommendations generated."


def test_report_summary_singular():
    report = RecommendationReport(
        recommendations=[Recommendation("x", "R001", "msg")]
    )
    assert "1 recommendation generated" in report.summary()


def test_report_by_code_filters():
    report = RecommendationReport(
        recommendations=[
            Recommendation("a", "R001", "m1"),
            Recommendation("b", "R002", "m2"),
            Recommendation("c", "R001", "m3"),
        ]
    )
    r001 = report.by_code("R001")
    assert len(r001) == 2
    assert all(r.code == "R001" for r in r001)


# ---------------------------------------------------------------------------
# build_recommendations
# ---------------------------------------------------------------------------

def test_every_minute_triggers_r001():
    job = _make_job("* * * * *")
    report = build_recommendations([job])
    codes = [r.code for r in report.recommendations]
    assert "R001" in codes


def test_specific_schedule_no_r001():
    job = _make_job("30 6 * * *")
    report = build_recommendations([job])
    codes = [r.code for r in report.recommendations]
    assert "R001" not in codes


def test_top_of_hour_pile_triggers_r002():
    jobs = [_make_job("0 2 * * *", command=f"cmd{i}", server="web") for i in range(4)]
    report = build_recommendations(jobs)
    codes = [r.code for r in report.recommendations]
    assert "R002" in codes


def test_top_of_hour_pile_below_threshold_no_r002():
    jobs = [_make_job("0 2 * * *", command=f"cmd{i}", server="web") for i in range(2)]
    report = build_recommendations(jobs)
    codes = [r.code for r in report.recommendations]
    assert "R002" not in codes


def test_invalid_job_triggers_r003():
    expr, _ = parse_cron_line("99 99 * * *")
    job = CronJob(
        server="srv1",
        schedule="99 99 * * *",
        command="bad",
        expression=expr,
        is_valid=False,
        tags=[],
    )
    report = build_recommendations([job])
    codes = [r.code for r in report.recommendations]
    assert "R003" in codes


def test_r001_suggestion_is_five_minute_interval():
    job = _make_job("* * * * *")
    report = build_recommendations([job])
    r001 = report.by_code("R001")
    assert r001[0].suggested_schedule == "*/5 * * * *"
