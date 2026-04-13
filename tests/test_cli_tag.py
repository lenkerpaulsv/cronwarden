"""Tests for cronwarden.cli_tag."""
from __future__ import annotations

import argparse
from unittest.mock import MagicMock, patch

import pytest

from cronwarden.cli_tag import add_tag_subcommand, _run_tag
from cronwarden.models import CronJob
from cronwarden.parser import parse_cron_line


def _make_job(command: str, tags: list[str], server: str = "srv") -> CronJob:
    expr = parse_cron_line("0 * * * *")
    return CronJob(schedule="0 * * * *", command=command, server=server, expression=expr, tags=tags)


def _make_ns(**kwargs) -> argparse.Namespace:
    defaults = dict(path="/fake", tags=[], match_all=False, list_tags=False, func=_run_tag)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_tag_subcommand_registers():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_tag_subcommand(sub)
    args = parser.parse_args(["tag", "/some/path"])
    assert hasattr(args, "func")


@patch("cronwarden.cli_tag._load")
def test_run_tag_list_tags(mock_load, capsys):
    mock_load.return_value = [
        _make_job("a.sh", ["backup"]),
        _make_job("b.sh", ["backup", "nightly"]),
    ]
    ns = _make_ns(list_tags=True)
    rc = _run_tag(ns)
    out = capsys.readouterr().out
    assert rc == 0
    assert "backup: 2" in out
    assert "nightly: 1" in out


@patch("cronwarden.cli_tag._load")
def test_run_tag_no_tags_prints_all(mock_load, capsys):
    mock_load.return_value = [
        _make_job("a.sh", ["web"]),
        _make_job("b.sh", ["db"]),
    ]
    ns = _make_ns()
    rc = _run_tag(ns)
    out = capsys.readouterr().out
    assert rc == 0
    assert "a.sh" in out
    assert "b.sh" in out


@patch("cronwarden.cli_tag._load")
def test_run_tag_filter_by_tag(mock_load, capsys):
    mock_load.return_value = [
        _make_job("a.sh", ["web"]),
        _make_job("b.sh", ["db"]),
    ]
    ns = _make_ns(tags=["web"])
    rc = _run_tag(ns)
    out = capsys.readouterr().out
    assert rc == 0
    assert "a.sh" in out
    assert "b.sh" not in out


@patch("cronwarden.cli_tag._load")
def test_run_tag_no_match_prints_message(mock_load, capsys):
    mock_load.return_value = [_make_job("a.sh", ["web"])]
    ns = _make_ns(tags=["db"])
    rc = _run_tag(ns)
    out = capsys.readouterr().out
    assert rc == 0
    assert "No matching" in out


@patch("cronwarden.cli_tag._load")
def test_run_tag_empty_list_tags(mock_load, capsys):
    mock_load.return_value = []
    ns = _make_ns(list_tags=True)
    rc = _run_tag(ns)
    out = capsys.readouterr().out
    assert rc == 0
    assert "No tags" in out
