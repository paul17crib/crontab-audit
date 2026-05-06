"""Detect duplicate crontab entries within and across hosts."""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from crontab_audit.parser import CrontabEntry


@dataclass
class DuplicateGroup:
    """A group of entries that share the same schedule and command."""
    schedule: str
    command: str
    entries: List[CrontabEntry] = field(default_factory=list)

    def __str__(self) -> str:
        hosts = ", ".join(e.host or "unknown" for e in self.entries)
        return f"[DUPLICATE] {self.schedule} {self.command!r} on: {hosts}"

    @property
    def is_cross_host(self) -> bool:
        """True if duplicates span more than one host."""
        hosts = {e.host for e in self.entries if e.host}
        return len(hosts) > 1

    @property
    def hosts(self) -> List[str]:
        return sorted({e.host or "unknown" for e in self.entries})


def _entry_key(entry: CrontabEntry) -> str:
    """Canonical key combining schedule fields and command."""
    schedule = " ".join([
        entry.minute, entry.hour, entry.dom, entry.month, entry.dow
    ])
    return f"{schedule}|{entry.command.strip()}"


def find_duplicates(entries: List[CrontabEntry]) -> List[DuplicateGroup]:
    """Find all duplicate entries (same schedule + command) in a flat list."""
    groups: Dict[str, DuplicateGroup] = {}
    for entry in entries:
        key = _entry_key(entry)
        schedule = " ".join([
            entry.minute, entry.hour, entry.dom, entry.month, entry.dow
        ])
        if key not in groups:
            groups[key] = DuplicateGroup(
                schedule=schedule,
                command=entry.command.strip(),
            )
        groups[key].entries.append(entry)
    return [g for g in groups.values() if len(g.entries) > 1]


def find_cross_host_duplicates(
    host_entries: Dict[str, List[CrontabEntry]]
) -> List[DuplicateGroup]:
    """Find entries with identical schedule+command across multiple hosts."""
    all_entries = []
    for host, entries in host_entries.items():
        for entry in entries:
            if entry.host is None:
                # Attach host name if not already set
                entry = CrontabEntry(
                    minute=entry.minute, hour=entry.hour, dom=entry.dom,
                    month=entry.month, dow=entry.dow, command=entry.command,
                    host=host, raw=entry.raw
                )
            all_entries.append(entry)
    duplicates = find_duplicates(all_entries)
    return [g for g in duplicates if g.is_cross_host]


def format_duplicate_report(groups: List[DuplicateGroup]) -> str:
    """Format a human-readable report of duplicate groups."""
    if not groups:
        return "No duplicate crontab entries found."
    lines = [f"Found {len(groups)} duplicate group(s):", ""]
    for g in groups:
        lines.append(str(g))
        for entry in g.entries:
            host = entry.host or "unknown"
            lines.append(f"  - [{host}] {entry.raw or entry.command}")
        lines.append("")
    return "\n".join(lines).rstrip()
