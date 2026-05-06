"""Detects crontab entries that may be stale or unused based on heuristics."""

from dataclasses import dataclass, field
from typing import List
from crontab_audit.parser import CrontabEntry


STALE_COMMAND_PATTERNS = [
    "/tmp/",
    "/var/tmp/",
    "test",
    "debug",
    "old",
    "bak",
    "backup_old",
    "deprecated",
    "disabled",
    "DISABLED",
    "TODO",
    "FIXME",
]

STALE_COMMENT_PATTERNS = [
    "deprecated",
    "disabled",
    "old",
    "remove",
    "fixme",
    "todo",
    "stale",
    "unused",
    "legacy",
]


@dataclass
class StalenessIssue:
    entry: CrontabEntry
    reason: str
    severity: str  # "warning" or "info"

    def __str__(self) -> str:
        host = f"[{self.entry.host}] " if self.entry.host else ""
        return (
            f"{self.severity.upper()} {host}"
            f"line {self.entry.lineno}: {self.entry.command!r} — {self.reason}"
        )


def _command_suggests_stale(command: str) -> List[str]:
    """Return list of matched stale patterns in the command string."""
    lower = command.lower()
    return [p for p in STALE_COMMAND_PATTERNS if p.lower() in lower]


def _comment_suggests_stale(comment: str) -> List[str]:
    """Return list of matched stale patterns in an inline comment."""
    lower = comment.lower()
    return [p for p in STALE_COMMENT_PATTERNS if p in lower]


def find_stale_entries(entries: List[CrontabEntry]) -> List[StalenessIssue]:
    """Scan entries for signs of staleness and return a list of issues."""
    issues: List[StalenessIssue] = []

    for entry in entries:
        command = entry.command

        # Check command path / content
        matched = _command_suggests_stale(command)
        if matched:
            issues.append(StalenessIssue(
                entry=entry,
                reason=f"command contains stale indicator(s): {matched}",
                severity="warning",
            ))
            continue

        # Check inline comment if present (e.g. command # deprecated)
        if "#" in command:
            _, _, inline = command.partition("#")
            matched_comments = _comment_suggests_stale(inline.strip())
            if matched_comments:
                issues.append(StalenessIssue(
                    entry=entry,
                    reason=f"inline comment suggests staleness: {matched_comments}",
                    severity="info",
                ))

    return issues
