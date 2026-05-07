"""Validates crontab schedule fields for semantic correctness beyond syntax."""
from dataclasses import dataclass, field
from typing import List
from crontab_audit.parser import CrontabEntry


@dataclass
class ScheduleIssue:
    entry: CrontabEntry
    field_name: str
    reason: str
    severity: str = "warning"  # 'warning' or 'error'

    def __str__(self) -> str:
        host = self.entry.host or "unknown"
        return (
            f"[{self.severity.upper()}] {host} | {self.entry.raw_schedule} "
            f"| field={self.field_name}: {self.reason}"
        )


_FIELD_RANGES = {
    "minute": (0, 59),
    "hour": (0, 23),
    "dom": (1, 31),
    "month": (1, 12),
    "dow": (0, 7),
}


def _check_field(value: str, name: str, lo: int, hi: int) -> List[str]:
    """Return list of problem strings for a single schedule field."""
    issues = []
    if value == "*":
        return issues
    for part in value.split(","):
        step = None
        if "/" in part:
            part, step_str = part.split("/", 1)
            if not step_str.isdigit():
                issues.append(f"non-numeric step '/{step_str}'")
                continue
            step = int(step_str)
            if step == 0:
                issues.append("step value of 0 is invalid")
                continue
        if "-" in part:
            bounds = part.split("-", 1)
            if not all(b.isdigit() for b in bounds):
                issues.append(f"non-numeric range '{part}'")
                continue
            a, b = int(bounds[0]), int(bounds[1])
            if a > b:
                issues.append(f"range start {a} > end {b}")
            if a < lo or b > hi:
                issues.append(f"range {a}-{b} out of bounds [{lo},{hi}]")
        elif part == "*":
            pass
        else:
            if not part.isdigit():
                issues.append(f"non-numeric value '{part}'")
                continue
            v = int(part)
            if v < lo or v > hi:
                issues.append(f"value {v} out of bounds [{lo},{hi}]")
    return issues


def validate_schedule(entry: CrontabEntry) -> List[ScheduleIssue]:
    """Return ScheduleIssue list for any out-of-range or malformed schedule fields."""
    results: List[ScheduleIssue] = []
    fields = entry.schedule_fields()
    names = ["minute", "hour", "dom", "month", "dow"]
    for name, value in zip(names, fields):
        lo, hi = _FIELD_RANGES[name]
        for reason in _check_field(value, name, lo, hi):
            results.append(ScheduleIssue(entry=entry, field_name=name, reason=reason))
    return results


def validate_all(entries: List[CrontabEntry]) -> List[ScheduleIssue]:
    """Run schedule validation across all entries."""
    issues: List[ScheduleIssue] = []
    for entry in entries:
        issues.extend(validate_schedule(entry))
    return issues
