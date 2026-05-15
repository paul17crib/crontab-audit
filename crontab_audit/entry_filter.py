"""Filter crontab entries by various criteria such as host, user, command pattern, or schedule field."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from crontab_audit.parser import CrontabEntry


@dataclass
class EntryFilter:
    """Criteria for filtering crontab entries."""

    host: Optional[str] = None
    user: Optional[str] = None
    command_pattern: Optional[str] = None
    minute: Optional[str] = None
    hour: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def matches(self, entry: CrontabEntry) -> bool:
        """Return True if the entry satisfies all filter criteria."""
        if self.host is not None:
            if getattr(entry, "host", None) != self.host:
                return False
        if self.user is not None:
            if getattr(entry, "user", None) != self.user:
                return False
        if self.command_pattern is not None:
            if not re.search(self.command_pattern, entry.command):
                return False
        if self.minute is not None:
            if entry.schedule_fields[0] != self.minute:
                return False
        if self.hour is not None:
            if entry.schedule_fields[1] != self.hour:
                return False
        if self.tags:
            entry_tags = set(
                t.lstrip("#").lower()
                for t in entry.command.split()
                if t.startswith("#tag:")
            )
            if not all(t.lower() in entry_tags for t in self.tags):
                return False
        return True


def apply_filter(entries: List[CrontabEntry], f: EntryFilter) -> List[CrontabEntry]:
    """Return entries that match the given filter."""
    return [e for e in entries if f.matches(e)]


def filter_by_host(entries: List[CrontabEntry], host: str) -> List[CrontabEntry]:
    return apply_filter(entries, EntryFilter(host=host))


def filter_by_command(entries: List[CrontabEntry], pattern: str) -> List[CrontabEntry]:
    return apply_filter(entries, EntryFilter(command_pattern=pattern))


def filter_by_user(entries: List[CrontabEntry], user: str) -> List[CrontabEntry]:
    return apply_filter(entries, EntryFilter(user=user))
