"""Filter and analyse crontab entries by time-of-day / day-of-week windows."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from crontab_audit.parser import CrontabEntry
from crontab_audit.overlap import _expand_field


@dataclass
class TimeWindow:
    """A named window defined by allowed hours and days-of-week."""
    name: str
    hours: List[int]          # 0-23
    days_of_week: List[int]   # 0-6  (0=Sunday)

    def matches(self, entry: CrontabEntry) -> bool:
        """Return True if *any* scheduled run of *entry* falls inside this window."""
        entry_hours = _expand_field(entry.schedule_fields[1], 0, 23)
        entry_days  = _expand_field(entry.schedule_fields[4], 0, 6)
        hours_overlap = bool(set(entry_hours) & set(self.hours))
        days_overlap  = bool(set(entry_days)  & set(self.days_of_week))
        return hours_overlap and days_overlap


@dataclass
class WindowMatch:
    entry: CrontabEntry
    window: TimeWindow

    def __str__(self) -> str:
        host = getattr(self.entry, 'host', 'unknown')
        return (
            f"[{host}] '{self.entry.command}' "
            f"runs inside window '{self.window.name}'"
        )


OFFICE_HOURS = TimeWindow(
    name="office-hours",
    hours=list(range(9, 18)),
    days_of_week=[1, 2, 3, 4, 5],
)

OFF_HOURS = TimeWindow(
    name="off-hours",
    hours=list(range(0, 9)) + list(range(18, 24)),
    days_of_week=[0, 1, 2, 3, 4, 5, 6],
)

WEEKEND = TimeWindow(
    name="weekend",
    hours=list(range(0, 24)),
    days_of_week=[0, 6],
)


def filter_by_window(
    entries: List[CrontabEntry],
    window: TimeWindow,
) -> List[CrontabEntry]:
    """Return only entries whose schedule overlaps *window*."""
    return [e for e in entries if window.matches(e)]


def find_window_matches(
    entries: List[CrontabEntry],
    windows: Optional[List[TimeWindow]] = None,
) -> List[WindowMatch]:
    """Return a WindowMatch for every (entry, window) pair that overlaps."""
    if windows is None:
        windows = [OFFICE_HOURS, OFF_HOURS, WEEKEND]
    results: List[WindowMatch] = []
    for entry in entries:
        for window in windows:
            if window.matches(entry):
                results.append(WindowMatch(entry=entry, window=window))
    return results
