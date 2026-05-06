"""Retention policy checker: flags crontab entries whose commands
write to paths that may lack a cleanup/rotation counterpart."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

from crontab_audit.parser import CrontabEntry

# Patterns that suggest a command is *writing* data somewhere
WRITE_PATTERNS = [
    re.compile(r">>?\s*[/~]"),          # shell redirect to a file
    re.compile(r"\btee\b"),             # tee writes to file
    re.compile(r"\bdump\b"),            # db dumps, etc.
    re.compile(r"\bbackup\b"),
    re.compile(r"\barchive\b"),
    re.compile(r"\blogrotate\b"),        # logrotate itself is fine, skip below
]

# Patterns that suggest a command is *cleaning up* data
CLEANUP_PATTERNS = [
    re.compile(r"\bfind\b.+\-delete\b"),
    re.compile(r"\bfind\b.+\-exec\s+rm\b"),
    re.compile(r"\brm\b"),
    re.compile(r"\btruncate\b"),
    re.compile(r"\blogrotate\b"),
    re.compile(r"\brotate\b"),
    re.compile(r"\bprune\b"),
    re.compile(r"\bclean\b"),
]


@dataclass
class RetentionIssue:
    entry: CrontabEntry
    reason: str

    def __str__(self) -> str:
        host = self.entry.host or "unknown"
        return f"[{host}] retention issue — {self.reason}: {self.entry.command}"


def _is_writer(command: str) -> bool:
    return any(p.search(command) for p in WRITE_PATTERNS)


def _is_cleanup(command: str) -> bool:
    return any(p.search(command) for p in CLEANUP_PATTERNS)


def find_retention_issues(
    entries: List[CrontabEntry],
) -> List[RetentionIssue]:
    """Return entries that write data but have no corresponding cleanup entry
    on the same host, or that explicitly look like writers without rotation."""
    issues: List[RetentionIssue] = []

    # Group by host
    by_host: dict[str | None, List[CrontabEntry]] = {}
    for e in entries:
        by_host.setdefault(e.host, []).append(e)

    for host, host_entries in by_host.items():
        writers = [e for e in host_entries if _is_writer(e.command)]
        has_cleanup = any(_is_cleanup(e.command) for e in host_entries)

        for w in writers:
            if not has_cleanup:
                issues.append(
                    RetentionIssue(
                        entry=w,
                        reason="data-writing command with no cleanup/rotation job on host",
                    )
                )

    return issues
