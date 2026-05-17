"""Archive crontab entries to a timestamped JSON file for historical tracking."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from crontab_audit.parser import CrontabEntry


@dataclass
class ArchiveRecord:
    archived_at: str
    host: Optional[str]
    user: Optional[str]
    schedule: str
    command: str

    def to_dict(self) -> dict:
        return {
            "archived_at": self.archived_at,
            "host": self.host,
            "user": self.user,
            "schedule": self.schedule,
            "command": self.command,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ArchiveRecord":
        return cls(
            archived_at=d["archived_at"],
            host=d.get("host"),
            user=d.get("user"),
            schedule=d["schedule"],
            command=d["command"],
        )

    def __str__(self) -> str:
        host_part = f"[{self.host}] " if self.host else ""
        return f"{self.archived_at} {host_part}{self.schedule} {self.command}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def archive_entries(
    entries: List[CrontabEntry],
    path: str,
    timestamp: Optional[str] = None,
) -> List[ArchiveRecord]:
    """Append entries to an archive file, returning the new records."""
    ts = timestamp or _now_iso()
    records = [
        ArchiveRecord(
            archived_at=ts,
            host=e.host,
            user=e.user,
            schedule=" ".join(e.schedule_fields),
            command=e.command,
        )
        for e in entries
    ]

    existing: List[dict] = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as fh:
            existing = json.load(fh)

    existing.extend(r.to_dict() for r in records)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(existing, fh, indent=2)

    return records


def load_archive(path: str) -> List[ArchiveRecord]:
    """Load all archive records from a file."""
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return [ArchiveRecord.from_dict(d) for d in data]


def filter_archive(
    records: List[ArchiveRecord],
    host: Optional[str] = None,
    command_fragment: Optional[str] = None,
) -> List[ArchiveRecord]:
    """Filter archive records by optional host or command substring."""
    result = records
    if host is not None:
        result = [r for r in result if r.host == host]
    if command_fragment is not None:
        result = [r for r in result if command_fragment in r.command]
    return result
