"""Command-line interface entry point for cronwarden."""

import argparse
import sys
from pathlib import Path

from cronwarden.loader import load_crontab_file, load_crontab_directory
from cronwarden.models import CronAuditResult
from cronwarden.conflict import detect_conflicts
from cronwarden.reporter import generate_report


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronwarden",
        description="Audit and validate cron job schedules across servers.",
    )
    p.add_argument(
        "path",
        help="Path to a crontab file or a directory of crontab files.",
    )
    p.add_argument(
        "--server",
        default="local",
        help="Server label to attach when loading a single file (default: local).",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    p.add_argument(
        "--output",
        metavar="FILE",
        default=None,
        help="Write report to FILE instead of stdout.",
    )
    p.add_argument(
        "--no-conflicts",
        action="store_true",
        help="Skip conflict detection.",
    )
    return p


def run(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    target = Path(args.path)
    if not target.exists():
        print(f"cronwarden: path not found: {target}", file=sys.stderr)
        return 2

    if target.is_dir():
        jobs, errors = load_crontab_directory(str(target))
    else:
        jobs, errors = load_crontab_file(str(target), server=args.server)

    audit_result = CronAuditResult(
        valid_jobs=jobs,
        invalid_jobs=errors,
    )

    conflicts = [] if args.no_conflicts else detect_conflicts(jobs)

    report = generate_report(
        audit_result=audit_result,
        conflicts=conflicts,
        output_format=args.format,
        outfile=args.output,
    )

    if args.output is None:
        print(report)

    return 1 if (errors or conflicts) else 0


def main():
    sys.exit(run())


if __name__ == "__main__":
    main()
