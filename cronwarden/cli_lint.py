"""CLI subcommand for linting cron jobs."""

from __future__ import annotations

import argparse
import sys

from cronwarden.loader import load_crontab_directory, load_crontab_file
from cronwarden.linter import lint_jobs


def add_lint_subcommand(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "lint",
        help="Lint cron job files for common issues and anti-patterns.",
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--file", metavar="PATH", help="Path to a single crontab file.")
    source.add_argument("--dir", metavar="PATH", help="Path to a directory of crontab files.")
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Exit with code 1 if any warnings are found.",
    )
    parser.set_defaults(func=_run_lint)


def _run_lint(args: argparse.Namespace) -> int:
    if args.file:
        jobs = load_crontab_file(args.file)
    else:
        jobs = load_crontab_directory(args.dir)

    result = lint_jobs(jobs)

    print(result.summary())
    for warning in result.warnings:
        print(f"  {warning}")

    if args.strict and result.has_warnings:
        return 1
    return 0


if __name__ == "__main__":
    import argparse as _ap

    _parser = _ap.ArgumentParser(prog="cronwarden-lint")
    _subs = _parser.add_subparsers()
    add_lint_subcommand(_subs)
    _args = _parser.parse_args()
    sys.exit(_args.func(_args))
