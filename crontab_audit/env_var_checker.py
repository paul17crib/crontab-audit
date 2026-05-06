"""Checks crontab entries for environment variable usage and potential issues."""

from dataclasses import dataclass, field
from typing import List, Optional
import re

from crontab_audit.parser import CrontabEntry


# Variables commonly expected in cron environments that may be missing
RISKY_ENV_REFS = {
    "$HOME", "$PATH", "$SHELL", "$USER", "$LOGNAME",
    "${HOME}", "${PATH}", "${SHELL}", "${USER}", "${LOGNAME}",
}

# Patterns that suggest hardcoded secrets or credentials
SECRET_PATTERNS = [
    re.compile(r'(?i)(password|passwd|secret|token|api[_-]?key)\s*=\s*\S+'),
    re.compile(r'(?i)--password[=\s]\S+'),
    re.compile(r'(?i)-p\s+\S{4,}'),
]


@dataclass
class EnvVarIssue:
    entry: CrontabEntry
    issue_type: str  # 'risky_ref' | 'hardcoded_secret' | 'undefined_var'
    detail: str

    def __str__(self) -> str:
        host = f"[{self.entry.host}] " if self.entry.host else ""
        return f"{host}{self.issue_type}: {self.detail} in command: {self.entry.command}"


def find_risky_env_refs(entry: CrontabEntry) -> List[EnvVarIssue]:
    """Flag commands that reference environment variables risky in cron context."""
    issues = []
    for ref in RISKY_ENV_REFS:
        if ref in entry.command:
            issues.append(EnvVarIssue(
                entry=entry,
                issue_type="risky_ref",
                detail=f"References '{ref}' which may be unset in cron environment",
            ))
    return issues


def find_hardcoded_secrets(entry: CrontabEntry) -> List[EnvVarIssue]:
    """Flag commands that appear to contain hardcoded credentials."""
    issues = []
    for pattern in SECRET_PATTERNS:
        match = pattern.search(entry.command)
        if match:
            issues.append(EnvVarIssue(
                entry=entry,
                issue_type="hardcoded_secret",
                detail=f"Possible hardcoded secret near '{match.group(0)[:30]}'",
            ))
    return issues


def check_entries(entries: List[CrontabEntry]) -> List[EnvVarIssue]:
    """Run all environment variable checks against a list of entries."""
    issues: List[EnvVarIssue] = []
    for entry in entries:
        issues.extend(find_risky_env_refs(entry))
        issues.extend(find_hardcoded_secrets(entry))
    return issues
