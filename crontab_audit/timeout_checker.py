"""Detects crontab entries that may run longer than their schedule interval,
potentially causing overlapping executions."""

from dataclasses import dataclass, field
from typing import List, Optional

from crontab_audit.parser import CrontabEntry
from crontab_audit.scheduler import classify_frequency, _field_min


# Approximate seconds per frequency label
_INTERVAL_SECONDS = {
    "minutely": 60,
    "every_5_min": 300,
    "every_10_min": 600,
    "every_15_min": 900,
    "every_30_min": 1800,
    "hourly": 3600,
    "daily": 86400,
    "weekly": 604800,
    "monthly": 2592000,
    "unknown": None,
}

# Heuristic: commands that tend to run long
_LONG_RUNNING_PATTERNS = [
    "rsync", "mysqldump", "pg_dump", "tar", "gzip", "bzip2",
    "find", "backup", "sync", "scp", "sftp", "wget", "curl",
    "python", "ruby", "perl", "bash", "sh",
]


@dataclass
class TimeoutIssue:
    entry: CrontabEntry
    frequency_label: str
    interval_seconds: Optional[int]
    reason: str
    severity: str = "warning"

    def __str__(self) -> str:
        host = self.entry.host or "unknown"
        cmd = self.entry.command
        return (
            f"[{self.severity.upper()}] {host}: '{cmd}' "
            f"(freq={self.frequency_label}) — {self.reason}"
        )


def _is_potentially_long_running(command: str) -> bool:
    """Return True if the command matches known long-running patterns."""
    lower = command.lower()
    return any(pat in lower for pat in _LONG_RUNNING_PATTERNS)


def check_timeout_risk(entries: List[CrontabEntry]) -> List[TimeoutIssue]:
    """Flag entries whose commands may outlast their schedule interval."""
    issues: List[TimeoutIssue] = []

    for entry in entries:
        label = classify_frequency(entry)
        interval = _INTERVAL_SECONDS.get(label)

        if interval is None:
            continue

        if interval <= 300 and _is_potentially_long_running(entry.command):
            reason = (
                f"Command may take longer than {interval}s interval; "
                "concurrent executions possible"
            )
            severity = "critical" if interval <= 60 else "warning"
            issues.append(
                TimeoutIssue(
                    entry=entry,
                    frequency_label=label,
                    interval_seconds=interval,
                    reason=reason,
                    severity=severity,
                )
            )

    return issues
