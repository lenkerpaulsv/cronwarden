"""CLI subcommand for diffing two crontab directories or files."""

import argparse
import sys

from cronwarden.loader import load_crontab_file, load_crontab_directory
from cronwarden.differ import diff_snapshots


def add_diff_subcommand(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "diff",
        help="Compare two crontab snapshots and report changes.",
    )
    parser.add_argument("old", help="Path to old crontab file or directory.")
    parser.add_argument("new", help="Path to new crontab file or directory.")
    parser.add_argument(
        "--server",
        default="unknown",
        help="Server label to use when loading files (default: unknown).",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print only the summary line instead of full diff.",
    )
    parser.set_defaults(func=_run_diff)


def _load(path: str, server: str):
    import os
    if os.path.isdir(path):
        return load_crontab_directory(path)
    return load_crontab_file(path, server=server)


def _run_diff(args: argparse.Namespace) -> int:
    old_jobs = _load(args.old, args.server)
    new_jobs = _load(args.new, args.server)

    result = diff_snapshots(old_jobs, new_jobs)

    if args.summary:
        print(result.summary())
    else:
        print(str(result))

    return 1 if result.has_changes else 0
