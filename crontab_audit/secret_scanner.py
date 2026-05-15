"""Scans crontab command fields for hardcoded secrets and sensitive tokens."""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List

from crontab_audit.parser import CrontabEntry

_PATTERNS: List[tuple[str, str]] = [
    (r"(?i)password\s*=\s*\S+", "hardcoded password"),
    (r"(?i)passwd\s*=\s*\S+", "hardcoded passwd"),
    (r"(?i)secret\s*=\s*\S+", "hardcoded secret"),
    (r"(?i)api[_-]?key\s*=\s*\S+", "hardcoded API key"),
    (r"(?i)token\s*=\s*\S+", "hardcoded token"),
    (r"(?i)auth\s*=\s*\S+", "hardcoded auth value"),
    (r"(?i)--password[=\s]\S+", "CLI password flag"),
    (r"(?i)-p\s+[^-]\S+", "short -p password flag"),
    (r"[A-Za-z0-9+/]{32,}={0,2}", "possible base64 secret"),
    (r"(?i)aws_secret_access_key\s*=\s*\S+", "AWS secret key"),
]


@dataclass
class SecretIssue:
    entry: CrontabEntry
    reason: str
    matched_text: str
    severity: str = "high"

    def __str__(self) -> str:
        host = self.entry.host or "unknown"
        return (
            f"[{self.severity.upper()}] {host}: {self.reason} "
            f"in command '{self.entry.command}' "
            f"(matched: '{self.matched_text}')"
        )


def scan_entry(entry: CrontabEntry) -> List[SecretIssue]:
    """Return all secret issues found in a single entry's command."""
    issues: List[SecretIssue] = []
    command = entry.command or ""
    for pattern, reason in _PATTERNS:
        match = re.search(pattern, command)
        if match:
            issues.append(
                SecretIssue(
                    entry=entry,
                    reason=reason,
                    matched_text=match.group(0)[:60],
                )
            )
    return issues


def scan_entries(entries: List[CrontabEntry]) -> List[SecretIssue]:
    """Scan all entries and return aggregated secret issues."""
    issues: List[SecretIssue] = []
    for entry in entries:
        issues.extend(scan_entry(entry))
    return issues
