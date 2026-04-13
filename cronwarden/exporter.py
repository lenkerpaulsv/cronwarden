"""Export audit results to various file formats (JSON, CSV, Markdown)."""

from __future__ import annotations

import csv
import io
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cronwarden.reporter import AuditReport


def export_json(report: "AuditReport", indent: int = 2) -> str:
    """Serialize the full audit report to a JSON string."""
    return json.dumps(report.to_json(), indent=indent)


def export_csv(report: "AuditReport") -> str:
    """Serialize audit results to CSV format.

    Columns: server, command, schedule, valid, invalid_reason, conflicts
    """
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(["server", "command", "schedule", "valid", "invalid_reason", "conflicts"])

    conflict_ids: set[str] = set()
    for cr in report.result.conflicts:
        conflict_ids.add(cr.job_a.identifier())
        conflict_ids.add(cr.job_b.identifier())

    for job in report.result.valid_jobs:
        has_conflict = job.identifier() in conflict_ids
        writer.writerow([job.server, job.command, str(job.expression), True, "", has_conflict])

    for job, reason in report.result.invalid_jobs:
        writer.writerow([job.server, job.command, "", False, reason, False])

    return output.getvalue()


def export_markdown(report: "AuditReport") -> str:
    """Serialize audit results to a Markdown report."""
    lines: list[str] = []
    lines.append("# CronWarden Audit Report\n")
    lines.append(report.summary() + "\n")

    lines.append("## Valid Jobs\n")
    lines.append("| Server | Command | Schedule |")
    lines.append("|--------|---------|----------|")
    for job in report.result.valid_jobs:
        lines.append(f"| {job.server} | {job.command} | {job.expression} |")

    lines.append("\n## Invalid Jobs\n")
    lines.append("| Server | Command | Reason |")
    lines.append("|--------|---------|--------|")
    for job, reason in report.result.invalid_jobs:
        lines.append(f"| {job.server} | {job.command} | {reason} |")

    lines.append("\n## Conflicts\n")
    if report.result.conflicts:
        lines.append("| Job A | Job B |")
        lines.append("|-------|-------|")
        for cr in report.result.conflicts:
            lines.append(f"| {cr.job_a.identifier()} | {cr.job_b.identifier()} |")
    else:
        lines.append("_No conflicts detected._")

    return "\n".join(lines) + "\n"


FORMAT_EXPORTERS = {
    "json": export_json,
    "csv": export_csv,
    "markdown": export_markdown,
}


def export(report: "AuditReport", fmt: str) -> str:
    """Export *report* in the requested *fmt* (json | csv | markdown)."""
    fmt = fmt.lower()
    if fmt not in FORMAT_EXPORTERS:
        raise ValueError(f"Unsupported export format: {fmt!r}. Choose from {list(FORMAT_EXPORTERS)}.")
    return FORMAT_EXPORTERS[fmt](report)
