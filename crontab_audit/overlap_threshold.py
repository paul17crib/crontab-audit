"""Overlap threshold checker: flags entries whose overlap count exceeds configurable limits."""

from dataclasses import dataclass, field
from typing import List, Dict

from crontab_audit.parser import CrontabEntry
from crontab_audit.overlap import OverlapResult


@dataclass
class ThresholdViolation:
    entry: CrontabEntry
    overlap_count: int
    threshold: int
    overlapping_with: List[CrontabEntry] = field(default_factory=list)

    def __str__(self) -> str:
        host = self.entry.host or "unknown"
        return (
            f"[THRESHOLD] {host}: '{self.entry.command}' overlaps {self.overlap_count} time(s) "
            f"(limit={self.threshold})"
        )


def check_overlap_thresholds(
    overlaps: List[OverlapResult],
    threshold: int = 3,
) -> List[ThresholdViolation]:
    """Return violations where an entry appears in more overlaps than allowed."""
    if threshold < 1:
        raise ValueError("threshold must be >= 1")

    # Count how many times each entry (by id) appears in overlaps
    count: Dict[int, int] = {}
    partners: Dict[int, List[CrontabEntry]] = {}

    for result in overlaps:
        a, b = result.entry_a, result.entry_b
        count[id(a)] = count.get(id(a), 0) + 1
        count[id(b)] = count.get(id(b), 0) + 1
        partners.setdefault(id(a), []).append(b)
        partners.setdefault(id(b), []).append(a)

    # Map id back to entry object
    entry_by_id: Dict[int, CrontabEntry] = {}
    for result in overlaps:
        entry_by_id[id(result.entry_a)] = result.entry_a
        entry_by_id[id(result.entry_b)] = result.entry_b

    violations: List[ThresholdViolation] = []
    seen = set()
    for eid, cnt in count.items():
        if cnt >= threshold and eid not in seen:
            seen.add(eid)
            violations.append(
                ThresholdViolation(
                    entry=entry_by_id[eid],
                    overlap_count=cnt,
                    threshold=threshold,
                    overlapping_with=partners.get(eid, []),
                )
            )

    violations.sort(key=lambda v: v.overlap_count, reverse=True)
    return violations
