"""Checks crontab entries for permission-related risks."""

from dataclasses import dataclass, field
from typing import List
from crontab_audit.parser import CrontabEntry

_SETUID_PATTERNS = ["chmod", "chown", "setuid", "setgid", "sudo", "su "]
_WORLD_WRITABLE = ["/tmp/", "/var/tmp/", "/dev/shm/"]
_SENSITIVE_PATHS = ["/etc/passwd", "/etc/shadow", "/etc/sudoers", "/root/", "/etc/cron"]


@dataclass
class PermissionIssue:
    entry: CrontabEntry
    reason: str
    severity: str  # "critical", "warning", "info"

    def __str__(self) -> str:
        host = self.entry.host or "unknown"
        return f"[{self.severity.upper()}] {host}: {self.entry.command!r} — {self.reason}"


def _check_setuid(entry: CrontabEntry) -> List[PermissionIssue]:
    issues = []
    cmd = entry.command.lower()
    for pat in _SETUID_PATTERNS:
        if pat in cmd:
            issues.append(PermissionIssue(
                entry=entry,
                reason=f"Command uses privilege-escalation pattern: '{pat}'",
                severity="critical",
            ))
            break
    return issues


def _check_world_writable(entry: CrontabEntry) -> List[PermissionIssue]:
    issues = []
    cmd = entry.command
    for path in _WORLD_WRITABLE:
        if path in cmd:
            issues.append(PermissionIssue(
                entry=entry,
                reason=f"Command writes to world-writable path: '{path}'",
                severity="warning",
            ))
    return issues


def _check_sensitive_paths(entry: CrontabEntry) -> List[PermissionIssue]:
    issues = []
    cmd = entry.command
    for path in _SENSITIVE_PATHS:
        if path in cmd:
            issues.append(PermissionIssue(
                entry=entry,
                reason=f"Command references sensitive path: '{path}'",
                severity="critical",
            ))
    return issues


def check_permissions(entries: List[CrontabEntry]) -> List[PermissionIssue]:
    """Run all permission checks against a list of crontab entries."""
    issues: List[PermissionIssue] = []
    for entry in entries:
        issues.extend(_check_setuid(entry))
        issues.extend(_check_world_writable(entry))
        issues.extend(_check_sensitive_paths(entry))
    return issues
