"""Detect overlapping crontab schedules across entries."""

from dataclasses import dataclass, field
from typing import List, Tuple
from .parser import CrontabEntry


@dataclass
class OverlapResult:
    entry_a: CrontabEntry
    entry_b: CrontabEntry
    reason: str

    def __str__(self) -> str:
        return (
            f"Overlap detected between '{self.entry_a.command}' "
            f"and '{self.entry_b.command}' on host '{self.entry_a.host}': {self.reason}"
        )


def _expand_field(value: str, min_val: int, max_val: int) -> set:
    """Expand a cron field into a set of integers it matches."""
    if value == "*":
        return set(range(min_val, max_val + 1))
    result = set()
    for part in value.split(","):
        if "/" in part:
            base, step = part.split("/", 1)
            step = int(step)
            if base == "*":
                start, end = min_val, max_val
            elif "-" in base:
                start, end = map(int, base.split("-", 1))
            else:
                start = end = int(base)
            result.update(range(start, end + 1, step))
        elif "-" in part:
            start, end = map(int, part.split("-", 1))
            result.update(range(start, end + 1))
        else:
            result.add(int(part))
    return result


def _schedules_overlap(a: CrontabEntry, b: CrontabEntry) -> bool:
    """Return True if two entries fire at any of the same times."""
    ranges = [
        (0, 59),   # minute
        (0, 23),   # hour
        (1, 31),   # day of month
        (1, 12),   # month
        (0, 6),    # day of week
    ]
    fields_a = a.schedule_fields()
    fields_b = b.schedule_fields()
    for i, (mn, mx) in enumerate(ranges):
        set_a = _expand_field(fields_a[i], mn, mx)
        set_b = _expand_field(fields_b[i], mn, mx)
        if not set_a & set_b:
            return False
    return True


def find_overlaps(entries: List[CrontabEntry]) -> List[OverlapResult]:
    """Find all pairs of entries with overlapping schedules on the same host."""
    results: List[OverlapResult] = []
    for i in range(len(entries)):
        for j in range(i + 1, len(entries)):
            a, b = entries[i], entries[j]
            if a.host != b.host:
                continue
            if _schedules_overlap(a, b):
                results.append(
                    OverlapResult(
                        entry_a=a,
                        entry_b=b,
                        reason="schedules share common execution times",
                    )
                )
    return results
