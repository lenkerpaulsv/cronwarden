"""CLI sub-command: cronwarden recommend

Prints schedule recommendations for jobs loaded from a file or directory.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from cronwarden.loader import load_crontab_directory, load_crontab_file
from cronwarden.models import CronJob
from cronwarden.recommender import build_recommendations


def add_recommend_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "recommend",
        help="Generate schedule recommendations for cron jobs.",
    )
    parser.add_argument(
        "path",
        help="Path to a crontab file or directory of crontab files.",
    )
    parser.add_argument(
        "--code",
        dest="code",
        default=None,
        help="Filter recommendations by code (e.g. R001).",
    )
    parser.set_defaults(func=_run_recommend)


def _load(path_str: str) -> List[CronJob]:
    p = Path(path_str)
    if p.is_dir():
        return load_crontab_directory(str(p))
    return load_crontab_file(str(p))


def _run_recommend(args: argparse.Namespace) -> int:
    jobs = _load(args.path)
    report = build_recommendations(jobs)

    recs = report.recommendations
    if args.code:
        recs = [r for r in recs if r.code == args.code]

    if not recs:
        print("No recommendations.")
        return 0

    print(report.summary())
    for rec in recs:
        print(" ", rec)
    return 0
