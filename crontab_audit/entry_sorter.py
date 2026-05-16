"""Sort and rank crontab entries by various criteria."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Callable
from crontab_audit.parser import CrontabEntry
from crontab_audit.scheduler import classify_frequency

_FREQUENCY_ORDER = {
    "minutely": 0,
    "hourly": 1,
    "daily": 2,
    "weekly": 3,
    "monthly": 4,
    "unknown": 5,
}


@dataclass
class SortedEntries:
    entries: List[CrontabEntry]
    sort_key: str
    reverse: bool = False

    def __str__(self) -> str:
        direction = "desc" if self.reverse else "asc"
        return f"SortedEntries(key={self.sort_key}, direction={direction}, count={len(self.entries)})"


def _key_by_host(entry: CrontabEntry) -> str:
    return (entry.host or "").lower()


def _key_by_user(entry: CrontabEntry) -> str:
    return (entry.user or "").lower()


def _key_by_command(entry: CrontabEntry) -> str:
    return entry.command.lower()


def _key_by_frequency(entry: CrontabEntry) -> int:
    label = classify_frequency(entry)
    return _FREQUENCY_ORDER.get(label, 5)


def _key_by_schedule(entry: CrontabEntry) -> str:
    return " ".join(entry.schedule_fields)


_SORT_KEYS: dict[str, Callable[[CrontabEntry], object]] = {
    "host": _key_by_host,
    "user": _key_by_user,
    "command": _key_by_command,
    "frequency": _key_by_frequency,
    "schedule": _key_by_schedule,
}


def sort_entries(
    entries: List[CrontabEntry],
    key: str = "host",
    reverse: bool = False,
) -> SortedEntries:
    """Sort entries by the given key. Raises ValueError for unknown keys."""
    if key not in _SORT_KEYS:
        raise ValueError(f"Unknown sort key '{key}'. Choose from: {list(_SORT_KEYS)}.")
    key_fn = _SORT_KEYS[key]
    sorted_list = sorted(entries, key=key_fn, reverse=reverse)
    return SortedEntries(entries=sorted_list, sort_key=key, reverse=reverse)


def available_sort_keys() -> List[str]:
    """Return the list of valid sort key names."""
    return list(_SORT_KEYS.keys())
