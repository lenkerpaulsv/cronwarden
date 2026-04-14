"""CLI sub-command: baseline — save or compare cron job baselines."""

from __future__ import annotations

import argparse
import sys

from cronwarden.loader import load_crontab_file, load_crontab_directory
from cronwarden.baseline import compare_to_baseline, save_baseline, load_baseline


def add_baseline_subcommand(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    parser = subparsers.add_parser(
        "baseline",
        help="Save or compare a cron-job baseline snapshot.",
    )
    parser.add_argument("path", help="Crontab file or directory to audit.")
    parser.add_argument(
        "--baseline-file",
        default=".cronwarden_baseline.json",
        metavar="FILE",
        help="Path to the baseline snapshot file (default: .cronwarden_baseline.json).",
    )
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument(
        "--save",
        action="store_true",
        help="Capture and save the current state as the new baseline.",
    )
    action.add_argument(
        "--compare",
        action="store_true",
        help="Compare the current state against the saved baseline.",
    )
    parser.set_defaults(func=_run_baseline)


def _load(path: str):
    import os
    if os.path.isdir(path):
        return load_crontab_directory(path)
    return load_crontab_file(path)


def _run_baseline(args: argparse.Namespace) -> int:
    jobs = _load(args.path)

    if args.save:
        snap = save_baseline(jobs, args.baseline_file)
        print(f"Baseline saved: {len(snap.jobs)} job(s) written to '{args.baseline_file}'.")
        return 0

    # --compare
    baseline = load_baseline(args.baseline_file)
    if baseline is None:
        print(
            f"No baseline found at '{args.baseline_file}'. "
            "Run with --save first.",
            file=sys.stderr,
        )
        return 2

    diff = compare_to_baseline(jobs, baseline)
    print(str(diff))
    return 1 if diff.has_changes else 0
