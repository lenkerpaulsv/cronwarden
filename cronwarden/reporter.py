"""Audit report formatting and output for cronwarden."""

from dataclasses import dataclass
from typing import List, Optional
import json

from cronwarden.models import CronAuditResult
from cronwarden.conflict import ConflictResult


@dataclass
class AuditReport:
    """Combined audit report with validation results and conflict detections."""
    audit_result: CronAuditResult
    conflicts: List[ConflictResult]

    @property
    def has_issues(self) -> bool:
        return bool(self.audit_result.invalid_jobs) or bool(self.conflicts)

    def summary(self) -> str:
        lines = []
        total = len(self.audit_result.valid_jobs) + len(self.audit_result.invalid_jobs)
        lines.append(f"=== CronWarden Audit Report ===")
        lines.append(f"Total jobs scanned : {total}")
        lines.append(f"Valid jobs         : {len(self.audit_result.valid_jobs)}")
        lines.append(f"Invalid jobs       : {len(self.audit_result.invalid_jobs)}")
        lines.append(f"Conflicts detected : {len(self.conflicts)}")
        return "\n".join(lines)

    def details(self) -> str:
        lines = [self.summary(), ""]
        if self.audit_result.invalid_jobs:
            lines.append("--- Invalid Jobs ---")
            for job, reason in self.audit_result.invalid_jobs:
                lines.append(f"  [{job.server}] {job.identifier()} -> {reason}")
            lines.append("")
        if self.conflicts:
            lines.append("--- Conflicts ---")
            for c in self.conflicts:
                lines.append(f"  {c}")
            lines.append("")
        if not self.has_issues:
            lines.append("No issues found. All cron jobs look healthy!")
        return "\n".join(lines)

    def to_json(self) -> str:
        data = {
            "summary": {
                "total": len(self.audit_result.valid_jobs) + len(self.audit_result.invalid_jobs),
                "valid": len(self.audit_result.valid_jobs),
                "invalid": len(self.audit_result.invalid_jobs),
                "conflicts": len(self.conflicts),
            },
            "invalid_jobs": [
                {"server": job.server, "id": job.identifier(), "reason": reason}
                for job, reason in self.audit_result.invalid_jobs
            ],
            "conflicts": [
                {
                    "job_a": {"server": c.job_a.server, "id": c.job_a.identifier()},
                    "job_b": {"server": c.job_b.server, "id": c.job_b.identifier()},
                    "reason": c.reason,
                }
                for c in self.conflicts
            ],
        }
        return json.dumps(data, indent=2)


def generate_report(
    audit_result: CronAuditResult,
    conflicts: List[ConflictResult],
    output_format: str = "text",
    outfile: Optional[str] = None,
) -> str:
    """Generate and optionally write a report. Returns the report string."""
    report = AuditReport(audit_result=audit_result, conflicts=conflicts)
    content = report.to_json() if output_format == "json" else report.details()
    if outfile:
        with open(outfile, "w") as fh:
            fh.write(content + "\n")
    return content
