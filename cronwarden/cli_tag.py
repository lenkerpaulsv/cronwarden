"""CLI sub-command: tag — list and filter jobs by tag."""
from __future__ import annotations

import argparse
import sys
from typing import List

from cronwarden.loader import load_crontab_directory, load_crontab_file
from cronwarden.models import CronJob
from cronwarden.tagger import build_tag_index, filter_by_tags


def add_tag_subcommand(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser("tag", help="List or filter jobs by tag")
    p.add_argument("path", help="Crontab file or directory")
    p.add_argument(
        "--tag",
        dest="tags",
        metavar="TAG",
        action="append",
        default=[],
        help="Filter by tag (repeatable)",
    )
    p.add_argument(
        "--all",
        dest="match_all",
        action="store_true",
        default=False,
        help="Job must carry ALL supplied tags (default: ANY)",
    )
    p.add_argument(
        "--list-tags",
        action="store_true",
        default=False,
        help="Print tag summary instead of job list",
    )
    p.set_defaults(func=_run_tag)


def _load(path: str) -> List[CronJob]:
    import os

    if os.path.isdir(path):
        return load_crontab_directory(path)
    return load_crontab_file(path)


def _run_tag(args: argparse.Namespace) -> int:
    jobs = _load(args.path)
    index = build_tag_index(jobs)

    if args.list_tags:
        summary = index.summary()
        if not summary:
            print("No tags found.")
        else:
            for tag, count in summary.items():
                print(f"{tag}: {count} job(s)")
        return 0

    if args.tags:
        jobs = filter_by_tags(jobs, args.tags, match_all=args.match_all)

    if not jobs:
        print("No matching jobs found.")
        return 0

    for job in jobs:
        tags_str = ", ".join(sorted(job.tags)) if job.tags else "—"
        print(f"[{job.server}] {job.schedule!r:30s} {job.command}  (tags: {tags_str})")

    return 0
