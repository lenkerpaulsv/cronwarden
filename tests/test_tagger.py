"""Tests for cronwarden.tagger."""
from __future__ import annotations

import pytest

from cronwarden.models import CronJob
from cronwarden.parser import parse_cron_line
from cronwarden.tagger import (
    TagIndex,
    build_tag_index,
    filter_by_tag,
    filter_by_tags,
)


def _make_job(command: str, tags: list[str], server: str = "srv1") -> CronJob:
    expr = parse_cron_line("* * * * *")
    return CronJob(schedule="* * * * *", command=command, server=server, expression=expr, tags=tags)


# ---------------------------------------------------------------------------
# TagIndex
# ---------------------------------------------------------------------------

def test_tag_index_empty_initially():
    idx = TagIndex()
    assert idx.all_tags() == []
    assert idx.jobs_for_tag("backup") == []


def test_tag_index_add_single_job():
    job = _make_job("backup.sh", ["backup", "nightly"])
    idx = TagIndex()
    idx.add(job)
    assert "backup" in idx.all_tags()
    assert "nightly" in idx.all_tags()
    assert idx.jobs_for_tag("backup") == [job]


def test_tag_index_multiple_jobs_same_tag():
    j1 = _make_job("a.sh", ["daily"])
    j2 = _make_job("b.sh", ["daily"])
    idx = build_tag_index([j1, j2])
    assert len(idx.jobs_for_tag("daily")) == 2


def test_tag_index_summary():
    jobs = [
        _make_job("a.sh", ["x", "y"]),
        _make_job("b.sh", ["x"]),
    ]
    idx = build_tag_index(jobs)
    s = idx.summary()
    assert s["x"] == 2
    assert s["y"] == 1


def test_tag_index_unknown_tag_returns_empty():
    idx = build_tag_index([_make_job("a.sh", ["foo"])])
    assert idx.jobs_for_tag("bar") == []


# ---------------------------------------------------------------------------
# filter_by_tag
# ---------------------------------------------------------------------------

def test_filter_by_tag_returns_matching():
    j1 = _make_job("a.sh", ["web"])
    j2 = _make_job("b.sh", ["db"])
    result = filter_by_tag([j1, j2], "web")
    assert result == [j1]


def test_filter_by_tag_no_match_returns_empty():
    j1 = _make_job("a.sh", ["web"])
    assert filter_by_tag([j1], "db") == []


# ---------------------------------------------------------------------------
# filter_by_tags
# ---------------------------------------------------------------------------

def test_filter_by_tags_any_match():
    j1 = _make_job("a.sh", ["web"])
    j2 = _make_job("b.sh", ["db"])
    j3 = _make_job("c.sh", ["cache"])
    result = filter_by_tags([j1, j2, j3], ["web", "db"], match_all=False)
    assert set(result) == {j1, j2}


def test_filter_by_tags_all_match():
    j1 = _make_job("a.sh", ["web", "nightly"])
    j2 = _make_job("b.sh", ["web"])
    result = filter_by_tags([j1, j2], ["web", "nightly"], match_all=True)
    assert result == [j1]


def test_filter_by_tags_empty_tag_list_returns_nothing():
    j1 = _make_job("a.sh", ["web"])
    # empty intersection with empty set
    result = filter_by_tags([j1], [], match_all=False)
    assert result == []
