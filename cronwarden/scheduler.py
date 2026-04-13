"""Next-run time calculation for cron expressions."""

from datetime import datetime, timedelta
from typing import Optional

from cronwarden.models import CronJob
from cronwarden.parser import CronExpression


def _next_values(field_str: str, lo: int, hi: int, current: int, reset: bool) -> tuple[int, bool]:
    """Return the next valid value for a cron field and whether it wrapped."""
    candidates = _expand_field(field_str, lo, hi)
    if not reset:
        forward = [v for v in candidates if v >= current]
        if forward:
            return forward[0], forward[0] != current
        return candidates[0], True  # wrap
    return candidates[0], False


def _expand_field(field_str: str, lo: int, hi: int) -> list[int]:
    """Expand a single cron field string into a sorted list of integers."""
    values: set[int] = set()
    for part in field_str.split(","):
        if part == "*":
            values.update(range(lo, hi + 1))
        elif "/" in part:
            base, step = part.split("/", 1)
            step = int(step)
            start = lo if base == "*" else int(base.split("-")[0])
            end = hi if base == "*" else (int(base.split("-")[1]) if "-" in base else hi)
            values.update(range(start, end + 1, step))
        elif "-" in part:
            a, b = part.split("-", 1)
            values.update(range(int(a), int(b) + 1))
        else:
            values.add(int(part))
    return sorted(values)


def next_run(expr: CronExpression, after: Optional[datetime] = None) -> datetime:
    """Return the next datetime at which *expr* would fire, after *after*."""
    if after is None:
        after = datetime.now()

    # Start one minute ahead (cron fires at the start of the minute)
    t = after.replace(second=0, microsecond=0) + timedelta(minutes=1)

    for _ in range(527040):  # max 1 year of minutes
        minute_ok = t.minute in _expand_field(expr.minute, 0, 59)
        hour_ok = t.hour in _expand_field(expr.hour, 0, 23)
        dom_ok = t.day in _expand_field(expr.day_of_month, 1, 31)
        month_ok = t.month in _expand_field(expr.month, 1, 12)
        dow_ok = t.weekday() in [d % 7 for d in _expand_field(expr.day_of_week, 0, 7)]

        if month_ok and dom_ok and dow_ok and hour_ok and minute_ok:
            return t
        t += timedelta(minutes=1)

    raise ValueError("Could not determine next run within one year")


def next_run_for_job(job: CronJob, after: Optional[datetime] = None) -> datetime:
    """Convenience wrapper that accepts a CronJob."""
    return next_run(job.expression, after)
