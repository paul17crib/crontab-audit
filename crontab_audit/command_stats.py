"""Aggregate statistics about commands across all crontab entries."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, List

from crontab_audit.parser import CrontabEntry


@dataclass
class CommandStats:
    """Statistics for a single command (or command prefix)."""

    command: str
    count: int
    hosts: List[str] = field(default_factory=list)
    entries: List[CrontabEntry] = field(default_factory=list)

    def __str__(self) -> str:
        host_list = ", ".join(sorted(set(self.hosts))) or "unknown"
        return f"{self.command!r}: {self.count} occurrence(s) on [{host_list}]"


def _command_key(command: str) -> str:
    """Return the base executable name from a command string."""
    parts = command.strip().split()
    if not parts:
        return ""
    # Strip leading env-var assignments like VAR=val
    for part in parts:
        if "=" not in part:
            return part.split("/")[-1]
    return parts[0]


def build_command_stats(entries: List[CrontabEntry]) -> Dict[str, CommandStats]:
    """Build a mapping of command key -> CommandStats from a list of entries."""
    stats: Dict[str, CommandStats] = {}
    for entry in entries:
        key = _command_key(entry.command)
        if key not in stats:
            stats[key] = CommandStats(command=key, count=0)
        stats[key].count += 1
        stats[key].hosts.append(entry.host or "")
        stats[key].entries.append(entry)
    return stats


def top_commands(entries: List[CrontabEntry], n: int = 10) -> List[CommandStats]:
    """Return the top-n most frequent commands across all entries."""
    stats = build_command_stats(entries)
    return sorted(stats.values(), key=lambda s: s.count, reverse=True)[:n]


def commands_by_host(entries: List[CrontabEntry]) -> Dict[str, List[str]]:
    """Return a mapping of host -> list of command keys seen on that host."""
    result: Dict[str, List[str]] = defaultdict(list)
    for entry in entries:
        host = entry.host or "unknown"
        result[host].append(_command_key(entry.command))
    return dict(result)
