"""CLI sub-command: watchdog — report stale cron jobs vs a saved snapshot."""

from __future__ import annotations

import argparse
import sys

from cronwarden.loader import load_crontab_file, load_crontab_directory
from cronwarden.snapshotter import load_snapshot, capture
from cronwarden.watchdog import check_stale


def add_watchdog_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "watchdog",
        help="Detect cron jobs missing since a baseline snapshot.",
    )
    p.add_argument("snapshot", help="Path to the baseline snapshot JSON file.")
    p.add_argument(
        "source",
        help="Crontab file or directory to treat as the current state.",
    )
    p.add_argument(
        "--threshold",
        type=int,
        default=7,
        metavar="DAYS",
        help="Number of days before a missing job is considered stale (default: 7).",
    )
    p.add_argument(
        "--server",
        default="local",
        help="Server name to assign when loading the current source.",
    )
    p.set_defaults(func=_run_watchdog)


def _load(source: str, server: str):
    import os

    if os.path.isdir(source):
        return load_crontab_directory(source)
    return load_crontab_file(source, server_name=server)


def _run_watchdog(args: argparse.Namespace) -> int:
    baseline_snapshot = load_snapshot(args.snapshot)
    current_jobs = _load(args.source, args.server)
    current_snapshot = capture(current_jobs)

    report = check_stale(current_snapshot, baseline_snapshot, threshold_days=args.threshold)
    print(report)
    return 1 if report.has_stale else 0
