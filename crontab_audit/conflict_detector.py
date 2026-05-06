"""Detects scheduling conflicts where two entries share the same command
but run at different, potentially conflicting intervals on the same host."""

from dataclasses import dataclass, field
from typing import List, Optional
from crontab_audit.parser import CrontabEntry
from crontab_audit.overlap import _expand_field


@dataclass
class ConflictIssue:
    host: str
    entry_a: CrontabEntry
    entry_b: CrontabEntry
    reason: str

    def __str__(self) -> str:
        return (
            f"[{self.host}] CONFLICT: '{self.entry_a.command}' "
            f"scheduled at '{self.entry_a.schedule_fields}' "
            f"and '{self.entry_b.schedule_fields}' — {self.reason}"
        )


def _command_key(entry: CrontabEntry) -> str:
    """Normalise command for comparison (strip leading env assignments)."""
    parts = entry.command.strip().split()
    for i, part in enumerate(parts):
        if "=" in part and not part.startswith("/"):
            continue
        return " ".join(parts[i:])
    return entry.command.strip()


def _minute_set(entry: CrontabEntry) -> set:
    fields = entry.schedule_fields.split()
    if len(fields) < 1:
        return set()
    return set(_expand_field(fields[0], 0, 59))


def _hour_set(entry: CrontabEntry) -> set:
    fields = entry.schedule_fields.split()
    if len(fields) < 2:
        return set()
    return set(_expand_field(fields[1], 0, 23))


def find_conflicts(entries: List[CrontabEntry]) -> List[ConflictIssue]:
    """Find entries on the same host with the same command but conflicting schedules."""
    issues: List[ConflictIssue] = []
    by_host: dict = {}

    for entry in entries:
        host = entry.host or "unknown"
        by_host.setdefault(host, []).append(entry)

    for host, host_entries in by_host.items():
        by_cmd: dict = {}
        for entry in host_entries:
            key = _command_key(entry)
            by_cmd.setdefault(key, []).append(entry)

        for cmd, cmd_entries in by_cmd.items():
            if len(cmd_entries) < 2:
                continue
            for i in range(len(cmd_entries)):
                for j in range(i + 1, len(cmd_entries)):
                    a, b = cmd_entries[i], cmd_entries[j]
                    if a.schedule_fields == b.schedule_fields:
                        continue  # exact duplicates handled elsewhere
                    mins_a = _minute_set(a)
                    mins_b = _minute_set(b)
                    hours_a = _hour_set(a)
                    hours_b = _hour_set(b)
                    if mins_a & mins_b and hours_a & hours_b:
                        issues.append(ConflictIssue(
                            host=host,
                            entry_a=a,
                            entry_b=b,
                            reason="overlapping minute+hour windows for same command",
                        ))
    return issues
