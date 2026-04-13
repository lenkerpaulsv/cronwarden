"""Write exported audit results to stdout or a file."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from cronwarden.exporter import export

if False:  # TYPE_CHECKING
    from cronwarden.reporter import AuditReport


_EXTENSION_MAP: dict[str, str] = {
    ".json": "json",
    ".csv": "csv",
    ".md": "markdown",
    ".markdown": "markdown",
}


def _infer_format(path: Path, fmt: Optional[str]) -> str:
    """Return explicit *fmt* or infer it from the file extension of *path*."""
    if fmt:
        return fmt
    ext = path.suffix.lower()
    if ext in _EXTENSION_MAP:
        return _EXTENSION_MAP[ext]
    raise ValueError(
        f"Cannot infer export format from extension {ext!r}. "
        "Pass --format explicitly."
    )


def write_report(
    report: "AuditReport",
    fmt: str,
    output_path: Optional[str] = None,
) -> None:
    """Render *report* in *fmt* and write to *output_path* (or stdout).

    Parameters
    ----------
    report:
        The :class:`~cronwarden.reporter.AuditReport` to export.
    fmt:
        One of ``json``, ``csv``, or ``markdown``.
    output_path:
        Filesystem path to write to.  ``None`` means stdout.
    """
    content = export(report, fmt)

    if output_path is None:
        sys.stdout.write(content)
        return

    path = Path(output_path)
    resolved_fmt = _infer_format(path, fmt)
    if resolved_fmt != fmt:
        # Re-render with inferred format if it differs.
        content = export(report, resolved_fmt)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
