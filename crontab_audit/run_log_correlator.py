"""Correlates crontab entries with run log data to detect missed or late runs."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime

from crontab_audit.parser import CrontabEntry


@dataclass
class RunLogEntry:
    host: str
    command: str
    scheduled_at: datetime
    ran_at: Optional[datetime]
    exit_code: Optional[int] = None

    def is_missed(self) -> bool:
        return self.ran_at is None

    def delay_seconds(self) -> Optional[float]:
        if self.ran_at is None or self.scheduled_at is None:
            return None
        return (self.ran_at - self.scheduled_at).total_seconds()


@dataclass
class CorrelationIssue:
    entry: CrontabEntry
    issue_type: str  # "missed", "late", "failed"
    detail: str
    run_log: Optional[RunLogEntry] = None

    def __str__(self) -> str:
        host = self.entry.host or "unknown"
        return f"[{self.issue_type.upper()}] {host}: {self.entry.command} — {self.detail}"


LATE_THRESHOLD_SECONDS = 120


def _command_key(command: str) -> str:
    parts = command.strip().split()
    if not parts:
        return ""
    token = parts[0]
    if "=" in token and len(parts) > 1:
        return parts[1]
    return token


def correlate_entries(
    entries: List[CrontabEntry],
    run_logs: List[RunLogEntry],
    late_threshold: float = LATE_THRESHOLD_SECONDS,
) -> List[CorrelationIssue]:
    """Match crontab entries to run log records and flag issues."""
    issues: List[CorrelationIssue] = []

    log_map: Dict[str, List[RunLogEntry]] = {}
    for log in run_logs:
        key = (log.host, _command_key(log.command))
        log_map.setdefault(key, []).append(log)

    for entry in entries:
        host = entry.host or "unknown"
        key = (host, _command_key(entry.command))
        matched_logs = log_map.get(key, [])

        if not matched_logs:
            issues.append(CorrelationIssue(
                entry=entry,
                issue_type="missed",
                detail="No run log records found for this entry.",
            ))
            continue

        for log in matched_logs:
            if log.is_missed():
                issues.append(CorrelationIssue(
                    entry=entry,
                    issue_type="missed",
                    detail="Scheduled run has no recorded execution time.",
                    run_log=log,
                ))
            elif log.exit_code is not None and log.exit_code != 0:
                issues.append(CorrelationIssue(
                    entry=entry,
                    issue_type="failed",
                    detail=f"Exited with code {log.exit_code}.",
                    run_log=log,
                ))
            else:
                delay = log.delay_seconds()
                if delay is not None and delay > late_threshold:
                    issues.append(CorrelationIssue(
                        entry=entry,
                        issue_type="late",
                        detail=f"Ran {delay:.0f}s after scheduled time.",
                        run_log=log,
                    ))

    return issues
