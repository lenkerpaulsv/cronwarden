"""CLI sub-command helpers for the 'export' command."""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from cronwarden.loader import load_crontab_directory, load_crontab_file
from cronwarden.conflict import detect_conflicts
from cronwarden.models import CronAuditResult
from cronwarden.reporter import AuditReport
from cronwarden.writer import write_report


def add_export_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the *export* sub-command on *subparsers*."""
    p = subparsers.add_parser(
        "export",
        help="Export audit results to a file or stdout.",
    )
    p.add_argument(
        "path",
        help="Path to a crontab file or directory of crontab files.",
    )
    p.add_argument(
        "--format",
        dest="fmt",
        choices=["json", "csv", "markdown"],
        default="json",
        help="Output format (default: json).",
    )
    p.add_argument(
        "--output",
        dest="output",
        default=None,
        help="Write output to this file instead of stdout.",
    )
    p.add_argument(
        "--server",
        dest="server",
        default="unknown",
        help="Server label used when loading a single file.",
    )
    p.set_defaults(func=_run_export)


def _run_export(args: argparse.Namespace) -> int:
    """Handler for the *export* sub-command.  Returns an exit code."""
    import os

    path = args.path
    if os.path.isdir(path):
        jobs = load_crontab_directory(path)
    else:
        jobs = load_crontab_file(path, server=args.server)

    valid_jobs = [j for j in jobs if j.expression is not None]
    invalid_jobs = [
        (j, "parse error") for j in jobs if j.expression is None
    ]
    conflicts = detect_conflicts(valid_jobs)

    result = CronAuditResult(
        valid_jobs=valid_jobs,
        invalid_jobs=invalid_jobs,
        conflicts=conflicts,
    )
    report = AuditReport(result)

    try:
        write_report(report, args.fmt, args.output)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    return 0
