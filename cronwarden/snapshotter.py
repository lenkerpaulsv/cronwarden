"""Snapshot module: capture and compare crontab states for drift detection."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from cronwarden.models import CronJob


@dataclass
class Snapshot:
    """A point-in-time capture of cron jobs across one or more servers."""

    taken_at: str
    jobs: List[Dict] = field(default_factory=list)

    @classmethod
    def capture(cls, jobs: List[CronJob]) -> "Snapshot":
        """Create a new snapshot from the given list of CronJob objects."""
        taken_at = datetime.now(timezone.utc).isoformat()
        serialized = [
            {
                "server": job.server,
                "command": job.command,
                "schedule": str(job.schedule),
                "identifier": job.identifier,
            }
            for job in jobs
        ]
        return cls(taken_at=taken_at, jobs=serialized)

    def to_dict(self) -> Dict:
        return {"taken_at": self.taken_at, "jobs": self.jobs}

    @classmethod
    def from_dict(cls, data: Dict) -> "Snapshot":
        return cls(taken_at=data["taken_at"], jobs=data.get("jobs", []))


def save_snapshot(snapshot: Snapshot, path: Path) -> None:
    """Persist a snapshot to a JSON file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(snapshot.to_dict(), fh, indent=2)


def load_snapshot(path: Path) -> Snapshot:
    """Load a previously saved snapshot from a JSON file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Snapshot file not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return Snapshot.from_dict(data)


def diff_snapshots(old: Snapshot, new: Snapshot) -> Dict:
    """Return a structured diff between two snapshots."""
    old_index: Dict[str, Dict] = {j["identifier"]: j for j in old.jobs}
    new_index: Dict[str, Dict] = {j["identifier"]: j for j in new.jobs}

    added = [j for k, j in new_index.items() if k not in old_index]
    removed = [j for k, j in old_index.items() if k not in new_index]
    changed = [
        {"old": old_index[k], "new": new_index[k]}
        for k in old_index
        if k in new_index and old_index[k] != new_index[k]
    ]

    return {
        "old_taken_at": old.taken_at,
        "new_taken_at": new.taken_at,
        "added": added,
        "removed": removed,
        "changed": changed,
        "has_drift": bool(added or removed or changed),
    }
