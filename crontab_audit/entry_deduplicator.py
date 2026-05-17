"""Deduplicates crontab entries within or across hosts by schedule+command key."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from crontab_audit.parser import CrontabEntry


@dataclass
class DeduplicationResult:
    """Result of a deduplication pass over a list of entries."""
    unique: List[CrontabEntry] = field(default_factory=list)
    duplicates: List[CrontabEntry] = field(default_factory=list)
    seen_keys: Dict[str, CrontabEntry] = field(default_factory=dict)

    @property
    def duplicate_count(self) -> int:
        return len(self.duplicates)

    @property
    def unique_count(self) -> int:
        return len(self.unique)

    def __str__(self) -> str:
        return (
            f"DeduplicationResult: {self.unique_count} unique, "
            f"{self.duplicate_count} duplicates removed"
        )


def _entry_key(entry: CrontabEntry, cross_host: bool = False) -> str:
    """Build a deduplication key from schedule fields and command.

    If cross_host is True, the host is excluded so identical jobs on different
    hosts are treated as duplicates.
    """
    schedule = " ".join(entry.schedule_fields)
    command = (entry.command or "").strip()
    if cross_host:
        return f"{schedule}|{command}"
    host = entry.host or ""
    return f"{host}|{schedule}|{command}"


def deduplicate_entries(
    entries: List[CrontabEntry],
    cross_host: bool = False,
    keep: str = "first",
) -> DeduplicationResult:
    """Remove duplicate entries from a list.

    Args:
        entries: Flat list of CrontabEntry objects.
        cross_host: When True, entries with the same schedule+command on
            different hosts are also considered duplicates.
        keep: 'first' keeps the first occurrence; 'last' keeps the last.

    Returns:
        A DeduplicationResult with unique and duplicate entries separated.
    """
    if keep not in ("first", "last"):
        raise ValueError("keep must be 'first' or 'last'")

    working = list(entries) if keep == "first" else list(reversed(entries))
    seen: Dict[str, CrontabEntry] = {}
    duplicates: List[CrontabEntry] = []

    for entry in working:
        key = _entry_key(entry, cross_host=cross_host)
        if key in seen:
            duplicates.append(entry)
        else:
            seen[key] = entry

    unique = list(seen.values())
    if keep == "last":
        unique = list(reversed(unique))
        duplicates = list(reversed(duplicates))

    result = DeduplicationResult(unique=unique, duplicates=duplicates, seen_keys=seen)
    return result
