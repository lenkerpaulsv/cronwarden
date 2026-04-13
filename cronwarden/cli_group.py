"""CLI subcommand: group — display cron jobs grouped by server, schedule, or command."""

from __future__ import annotations

import argparse
import sys
from typing import List

from cronwarden.loader import load_crontab_file, load_crontab_directory
from cronwarden.grouper import group_by_server, group_by_schedule, group_by_command_prefix
from cronwarden.models import CronJob

_STRATEGIES = {
    "server": group_by_server,
    "schedule": group_by_schedule,
    "command": group_by_command_prefix,
}


def add_group_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "group",
        help="Group cron jobs by server, schedule, or command prefix.",
    )
    p.add_argument("path", help="Crontab file or directory to load.")
    p.add_argument(
        "--by",
        choices=list(_STRATEGIES.keys()),
        default="server",
        help="Grouping strategy (default: server).",
    )
    p.add_argument(
        "--dir",
        action="store_true",
        help="Treat path as a directory of crontab files.",
    )
    p.set_defaults(func=_run_group)


def _load(path: str, is_dir: bool) -> List[CronJob]:
    if is_dir:
        return load_crontab_directory(path)
    return load_crontab_file(path)


def _run_group(args: argparse.Namespace) -> int:
    jobs = _load(args.path, args.dir)
    strategy = _STRATEGIES[args.by]
    index = strategy(jobs)

    if len(index) == 0:
        print("No jobs found.")
        return 0

    print(index.summary())
    print()
    for key in index.keys():
        print(str(index.get(key)))
        print()

    return 0
