"""Snapshot utilities: save and load crontab state for diffing over time."""

import json
from pathlib import Path
from typing import List
from crontab_audit.loader import HostCrontab
from crontab_audit.parser import CrontabEntry


def _entry_to_dict(entry: CrontabEntry) -> dict:
    return {
        "minute": entry.minute,
        "hour": entry.hour,
        "day_of_month": entry.day_of_month,
        "month": entry.month,
        "day_of_week": entry.day_of_week,
        "command": entry.command,
        "raw": entry.raw,
        "hostname": entry.hostname,
    }


def _entry_from_dict(d: dict) -> CrontabEntry:
    return CrontabEntry(
        minute=d["minute"],
        hour=d["hour"],
        day_of_month=d["day_of_month"],
        month=d["month"],
        day_of_week=d["day_of_week"],
        command=d["command"],
        raw=d.get("raw", ""),
        hostname=d.get("hostname", ""),
    )


def save_snapshot(hosts: List[HostCrontab], path: str) -> None:
    """Serialize a list of HostCrontab objects to a JSON snapshot file."""
    data = [
        {
            "hostname": h.hostname,
            "entries": [_entry_to_dict(e) for e in h.entries],
            "parse_errors": [str(err) for err in h.parse_errors],
        }
        for h in hosts
    ]
    Path(path).write_text(json.dumps(data, indent=2))


def load_snapshot(path: str) -> List[HostCrontab]:
    """Load a list of HostCrontab objects from a JSON snapshot file."""
    raw = json.loads(Path(path).read_text())
    hosts = []
    for item in raw:
        entries = [_entry_from_dict(e) for e in item.get("entries", [])]
        hosts.append(
            HostCrontab(
                hostname=item["hostname"],
                entries=entries,
                parse_errors=[],
            )
        )
    return hosts
