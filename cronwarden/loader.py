"""Crontab file loader for cronwarden."""

import os
from pathlib import Path
from typing import List

from cronwarden.models import CronAuditResult, CronJob
from cronwarden.parser import parse_cron_line

DEFAULT_USER = "root"


def load_crontab_file(filepath: str, server: str, user: str = DEFAULT_USER) -> CronAuditResult:
    """Load and parse a crontab file, returning an audit result."""
    path = Path(filepath)
    result = CronAuditResult(server=server, source_file=str(path))

    if not path.exists():
        result.parse_errors.append(f"File not found: {filepath}")
        return result

    if not path.is_file():
        result.parse_errors.append(f"Not a file: {filepath}")
        return result

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        result.parse_errors.append(f"Cannot read file '{filepath}': {exc}")
        return result

    for line_num, raw_line in enumerate(lines, start=1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("@"):
            result.parse_errors.append(
                f"Line {line_num}: Macro syntax '@...' not yet supported: '{stripped}'"
            )
            continue
        expression = parse_cron_line(stripped)
        if expression is None:
            continue
        job = CronJob(
            server=server,
            user=user,
            schedule=f"{expression.minute} {expression.hour} {expression.day_of_month} "
                     f"{expression.month} {expression.day_of_week}",
            command=expression.command,
            source_file=str(path),
            line_number=line_num,
            is_valid=expression.is_valid,
            validation_error=expression.error,
        )
        result.jobs.append(job)

    return result


def load_crontab_directory(directory: str, server: str) -> List[CronAuditResult]:
    """Load all crontab files from a directory (e.g. /etc/cron.d/)."""
    results = []
    dir_path = Path(directory)
    if not dir_path.is_dir():
        return results
    for entry in sorted(dir_path.iterdir()):
        if entry.is_file() and not entry.name.startswith("."):
            results.append(load_crontab_file(str(entry), server=server, user=DEFAULT_USER))
    return results
