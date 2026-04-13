"""Human-readable schedule description formatter for cron expressions."""

from cronwarden.parser import CronExpression

_MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

_DOW_NAMES = [
    "ndef __field(value: str, unit: str,: list[str] | None = None) -> str:
    """Return a human-readable description for a single cron field."""
    if value == "*":
        return f"every {unit}"

    if value.startswith("*/"):
        step = value[2:]
        return f"every {step} {unit}s"

    if "-" in value and "/" in value:
        range_part, step = value.split("/")
        start, end = range_part.split("-")
        if names:
            start = names[int(start)] if int(start) < len(names) else start
            end = names[int(end)] if int(end) < len(names) else end
        return f"every {step} {unit}s from {start} to {end}"

    if "-" in value:
        start, end = value.split("-")
        if names:
            start = names[int(start)] if int(start) < len(names) else start
            end = names[int(end)] if int(end) < len(names) else end
        return f"{unit}s {start} through {end}"

    if "," in value:
        parts = value.split(",")
        if names:
            parts = [names[int(p)] if int(p) < len(names) else p for p in parts]
        return f"{unit}s " + ", ".join(parts)

    if names:
        idx = int(value)
        label = names[idx] if idx < len(names) else value
        return f"on {unit} {label}"

    return f"at {unit} {value}"


def describe_schedule(expr: CronExpression) -> str:
    """Return a plain-English description of a CronExpression."""
    minute = _describe_field(expr.minute, "minute")
    hour = _describe_field(expr.hour, "hour")
    dom = _describe_field(expr.day_of_month, "day-of-month")
    month = _describe_field(expr.month, "month", _MONTH_NAMES)
    dow = _describe_field(expr.day_of_week, "weekday", _DOW_NAMES)

    parts = []
    if expr.minute == "*" and expr.hour == "*":
        parts.append("every minute")
    elif expr.minute == "*":
        parts.append(f"{minute}, {hour}")
    else:
        parts.append(f"{minute} past {hour}")

    if expr.day_of_month != "*":
        parts.append(dom)
    if expr.month != "*":
        parts.append(month)
    if expr.day_of_week != "*":
        parts.append(dow)

    return ", ".join(parts)
