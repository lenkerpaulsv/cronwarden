"""CLI sub-command: show upcoming schedule for loaded cron jobs."""

import argparse
from datetime import datetime

from cronwarden.loader import load_crontab_file, load_crontab_directory
from cronwarden.schedule_table import upcoming_runs, format_table


def add_schedule_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "schedule",
        help="Show the next N upcoming runs for each cron job.",
    )
    p.add_argument("path", help="Crontab file or directory to load.")
    p.add_argument(
        "-n",
        "--count",
        type=int,
        default=3,
        metavar="N",
        help="Number of upcoming runs to show per job (default: 3).",
    )
    p.add_argument(
        "--after",
        default=None,
        metavar="DATETIME",
        help="ISO-format datetime to use as 'now' (e.g. 2024-01-15T08:00).",
    )
    p.add_argument(
        "--server",
        default=None,
        help="Filter jobs to a specific server name.",
    )
    p.set_defaults(func=_run_schedule)


def _run_schedule(args: argparse.Namespace) -> int:
    import os

    path = args.path
    if os.path.isdir(path):
        jobs = load_crontab_directory(path)
    else:
        jobs = load_crontab_file(path)

    if args.server:
        jobs = [j for j in jobs if j.server == args.server]

    after: datetime | None = None
    if args.after:
        try:
            after = datetime.fromisoformat(args.after)
        except ValueError:
            print(f"Invalid --after value: {args.after!r}. Use ISO format, e.g. 2024-01-15T08:00.")
            return 1

    rows = upcoming_runs(jobs, n=args.count, after=after)
    print(format_table(rows))
    return 0
