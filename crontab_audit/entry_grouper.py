"""Groups crontab entries by various criteria for analysis."""

from collections import defaultdict
from typing import Dict, List, Optional
from crontab_audit.parser import CrontabEntry
from crontab_audit.scheduler import classify_frequency


class EntryGroup:
    """A named group of crontab entries."""

    def __init__(self, key: str, entries: List[CrontabEntry]) -> None:
        self.key = key
        self.entries = entries

    def __len__(self) -> int:
        return len(self.entries)

    def __str__(self) -> str:
        return f"EntryGroup({self.key!r}, {len(self.entries)} entries)"


def group_by_host(entries: List[CrontabEntry]) -> Dict[str, EntryGroup]:
    """Group entries by their host attribute."""
    buckets: Dict[str, List[CrontabEntry]] = defaultdict(list)
    for entry in entries:
        key = entry.host or "(unknown)"
        buckets[key].append(entry)
    return {k: EntryGroup(k, v) for k, v in sorted(buckets.items())}


def group_by_user(entries: List[CrontabEntry]) -> Dict[str, EntryGroup]:
    """Group entries by their user attribute."""
    buckets: Dict[str, List[CrontabEntry]] = defaultdict(list)
    for entry in entries:
        key = entry.user or "(unknown)"
        buckets[key].append(entry)
    return {k: EntryGroup(k, v) for k, v in sorted(buckets.items())}


def group_by_frequency(entries: List[CrontabEntry]) -> Dict[str, EntryGroup]:
    """Group entries by their classified frequency label."""
    buckets: Dict[str, List[CrontabEntry]] = defaultdict(list)
    for entry in entries:
        label = classify_frequency(entry)
        buckets[label].append(entry)
    return {k: EntryGroup(k, v) for k, v in sorted(buckets.items())}


def group_by_hour(entries: List[CrontabEntry]) -> Dict[str, EntryGroup]:
    """Group entries by the hour field of their schedule."""
    buckets: Dict[str, List[CrontabEntry]] = defaultdict(list)
    for entry in entries:
        hour = entry.schedule_fields[1] if len(entry.schedule_fields) > 1 else "*"
        buckets[hour].append(entry)
    return {k: EntryGroup(k, v) for k, v in sorted(buckets.items())}


def group_entries(entries: List[CrontabEntry], by: str) -> Dict[str, EntryGroup]:
    """Dispatch grouping by a named key."""
    dispatch = {
        "host": group_by_host,
        "user": group_by_user,
        "frequency": group_by_frequency,
        "hour": group_by_hour,
    }
    if by not in dispatch:
        raise ValueError(f"Unknown grouping key {by!r}. Choose from: {sorted(dispatch)}.")
    return dispatch[by](entries)
