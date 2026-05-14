"""Detects crontab entries that may cause resource contention."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
from crontab_audit.parser import CrontabEntry

HEAVY_COMMANDS = (
    "rsync", "mysqldump", "pg_dump", "tar", "gzip", "bzip2",
    "find", "du", "dd", "ffmpeg", "convert", "python", "ruby",
    "java", "node", "php", "perl", "rake", "bundle exec",
)

HIGH_IO_PATTERNS = (">/dev/", ">> /", "tee ", "cp -r", "mv ", "rm -rf")


@dataclass
class ResourceIssue:
    entry: CrontabEntry
    reason: str
    severity: str  # 'high' | 'medium' | 'low'

    def __str__(self) -> str:
        host = self.entry.host or "unknown"
        return (
            f"[{self.severity.upper()}] {host}: `{self.entry.command}` "
            f"({self.entry.raw_schedule}) — {self.reason}"
        )


def _is_heavy_command(command: str) -> bool:
    cmd_lower = command.lower()
    return any(kw in cmd_lower for kw in HEAVY_COMMANDS)


def _is_high_io(command: str) -> bool:
    return any(pat in command for pat in HIGH_IO_PATTERNS)


def _runs_frequently(entry: CrontabEntry) -> bool:
    """True if the entry runs more than once per hour."""
    minute = entry.schedule_fields[0]
    hour = entry.schedule_fields[1]
    if hour == "*" and minute == "*":
        return True
    if "/" in minute:
        try:
            step = int(minute.split("/")[1])
            return step < 30
        except (ValueError, IndexError):
            pass
    return False


def check_resource_risk(entries: List[CrontabEntry]) -> List[ResourceIssue]:
    issues: List[ResourceIssue] = []
    for entry in entries:
        heavy = _is_heavy_command(entry.command)
        high_io = _is_high_io(entry.command)
        frequent = _runs_frequently(entry)

        if heavy and frequent:
            issues.append(ResourceIssue(
                entry=entry,
                reason="Heavy process scheduled at high frequency",
                severity="high",
            ))
        elif heavy and high_io:
            issues.append(ResourceIssue(
                entry=entry,
                reason="Heavy process with high I/O activity",
                severity="medium",
            ))
        elif frequent and high_io:
            issues.append(ResourceIssue(
                entry=entry,
                reason="High-frequency entry with significant I/O",
                severity="medium",
            ))
        elif heavy:
            issues.append(ResourceIssue(
                entry=entry,
                reason="Potentially resource-intensive command",
                severity="low",
            ))
    return issues
