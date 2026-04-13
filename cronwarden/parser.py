"""Cron expression parser and validator for cronwarden."""

import re
from dataclasses import dataclass
from typing import Optional

CRON_FIELD_RANGES = {
    "minute": (0, 59),
    "hour": (0, 23),
    "day_of_month": (1, 31),
    "month": (1, 12),
    "day_of_week": (0, 7),
}

MONTH_ALIASES = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "may": 5, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

DOW_ALIASES = {
    "sun": 0, "mon": 1, "tue": 2, "wed": 3,
    "thu": 4, "fri": 5, "sat": 6,
}


@dataclass
class CronExpression:
    raw: str
    minute: str
    hour: str
    day_of_month: str
    month: str
    day_of_week: str
    command: str
    is_valid: bool = True
    error: Optional[str] = None


def _resolve_aliases(value: str, aliases: dict) -> str:
    for alias, num in aliases.items():
        value = re.sub(rf"\b{alias}\b", str(num), value, flags=re.IGNORECASE)
    return value


def _validate_field(value: str, field_name: str) -> Optional[str]:
    min_val, max_val = CRON_FIELD_RANGES[field_name]
    if value == "*":
        return None
    parts = value.split(",")
    for part in parts:
        if "/" in part:
            base, step = part.split("/", 1)
            if not step.isdigit():
                return f"Invalid step '{step}' in field '{field_name}'"
            if base != "*" and "-" not in base:
                if not base.isdigit() or not (min_val <= int(base) <= max_val):
                    return f"Value '{base}' out of range for '{field_name}'"
        elif "-" in part:
            bounds = part.split("-")
            if len(bounds) != 2 or not all(b.isdigit() for b in bounds):
                return f"Invalid range '{part}' in field '{field_name}'"
            lo, hi = int(bounds[0]), int(bounds[1])
            if not (min_val <= lo <= max_val) or not (min_val <= hi <= max_val) or lo > hi:
                return f"Range '{part}' out of bounds for '{field_name}'"
        else:
            if not part.isdigit() or not (min_val <= int(part) <= max_val):
                return f"Value '{part}' out of range for '{field_name}' ({min_val}-{max_val})"
    return None


def parse_cron_line(line: str) -> Optional[CronExpression]:
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    parts = line.split(None, 5)
    if len(parts) < 6:
        return CronExpression(
            raw=line, minute="", hour="", day_of_month="",
            month="", day_of_week="", command="",
            is_valid=False, error="Cron line must have at least 5 time fields and a command"
        )
    minute, hour, dom, month, dow = parts[:5]
    command = parts[5]
    month = _resolve_aliases(month, MONTH_ALIASES)
    dow = _resolve_aliases(dow, DOW_ALIASES)
    fields = {"minute": minute, "hour": hour, "day_of_month": dom, "month": month, "day_of_week": dow}
    for field_name, value in fields.items():
        err = _validate_field(value, field_name)
        if err:
            return CronExpression(raw=line, minute=minute, hour=hour, day_of_month=dom,
                                  month=month, day_of_week=dow, command=command,
                                  is_valid=False, error=err)
    return CronExpression(raw=line, minute=minute, hour=hour, day_of_month=dom,
                          month=month, day_of_week=dow, command=command)
