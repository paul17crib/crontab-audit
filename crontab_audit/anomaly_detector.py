"""Detects anomalous crontab entries based on unusual scheduling patterns."""
from dataclasses import dataclass, field
from typing import List, Optional
from crontab_audit.parser import CrontabEntry


@dataclass
class AnomalyIssue:
    entry: CrontabEntry
    reason: str
    severity: str  # "low", "medium", "high"

    def __str__(self) -> str:
        host = self.entry.host or "unknown"
        return f"[{self.severity.upper()}] {host}: {self.entry.command!r} — {self.reason}"


def _is_odd_minute(entry: CrontabEntry) -> Optional[str]:
    """Flag entries scheduled at unusual minutes like 3, 7, 13."""
    minute = entry.schedule_fields[0]
    try:
        val = int(minute)
        if val not in (0, 5, 10, 15, 20, 30, 45) and val > 0:
            return f"Unusual minute value: {val}"
    except ValueError:
        pass
    return None


def _is_rarely_used_dow(entry: CrontabEntry) -> Optional[str]:
    """Flag entries that only run on day 6 (Saturday) or 0 (Sunday) alone."""
    dow = entry.schedule_fields[4]
    if dow in ("6", "0", "7"):
        return f"Runs only on a single weekend day (dow={dow})"
    return None


def _is_suspicious_interval(entry: CrontabEntry) -> Optional[str]:
    """Flag step values that are unusual, e.g. */3, */7."""
    for f in entry.schedule_fields:
        if f.startswith("*/"):
            try:
                step = int(f[2:])
                if step not in (1, 2, 5, 10, 15, 20, 30):
                    return f"Unusual step interval: {f}"
            except ValueError:
                pass
    return None


def detect_anomalies(entries: List[CrontabEntry]) -> List[AnomalyIssue]:
    """Run all anomaly checks and return a list of issues."""
    issues: List[AnomalyIssue] = []
    checks = [
        (_is_odd_minute, "medium"),
        (_is_rarely_used_dow, "low"),
        (_is_suspicious_interval, "low"),
    ]
    for entry in entries:
        for check_fn, severity in checks:
            reason = check_fn(entry)
            if reason:
                issues.append(AnomalyIssue(entry=entry, reason=reason, severity=severity))
    return issues
