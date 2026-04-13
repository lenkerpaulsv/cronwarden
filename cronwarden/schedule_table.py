"""Build a human-readable upcoming-schedule table for a list of CronJobs."""

from datetime import datetime
from typing import Optional

from cronwarden.models import CronJob
from cronwarden.scheduler import next_run_for_job


def upcoming_runs(
    jobs: list[CronJob],
    n: int = 5,
    after: Optional[datetime] = None,
) -> list[dict]:
    """Return a list of dicts describing the next *n* runs for each job."""
    if after is None:
        after = datetime.now()

    rows = []
    for job in jobs:
        try:
            t = after
            for _ in range(n):
                t = next_run_for_job(job, after=t)
                rows.append(
                    {
                        "server": job.server,
                        "identifier": job.identifier,
                        "command": job.command,
                        "next_run": t.strftime("%Y-%m-%d %H:%M"),
                    }
                )
        except ValueError:
            rows.append(
                {
                    "server": job.server,
                    "identifier": job.identifier,
                    "command": job.command,
                    "next_run": "N/A",
                }
            )
    return rows


def format_table(rows: list[dict]) -> str:
    """Render *rows* as a fixed-width text table."""
    if not rows:
        return "No upcoming runs."

    headers = ["Server", "Job", "Command", "Next Run"]
    keys = ["server", "identifier", "command", "next_run"]
    widths = [len(h) for h in headers]
    for row in rows:
        for i, k in enumerate(keys):
            widths[i] = max(widths[i], len(str(row.get(k, ""))))

    sep = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    header_row = "| " + " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers)) + " |"
    lines = [sep, header_row, sep]
    for row in rows:
        line = "| " + " | ".join(str(row.get(k, "")).ljust(widths[i]) for i, k in enumerate(keys)) + " |"
        lines.append(line)
    lines.append(sep)
    return "\n".join(lines)
