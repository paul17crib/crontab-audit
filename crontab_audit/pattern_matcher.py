"""Pattern-based command matching for crontab entries."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from crontab_audit.parser import CrontabEntry


@dataclass
class PatternMatch:
    entry: CrontabEntry
    pattern: str
    label: str
    description: str

    def __str__(self) -> str:
        host = self.entry.host or "unknown"
        return (
            f"[{self.label}] {host}: {self.entry.command!r} "
            f"matched pattern {self.pattern!r} — {self.description}"
        )


_BUILTIN_PATTERNS: List[dict] = [
    {
        "pattern": r"\brm\s+-rf\b",
        "label": "destructive",
        "description": "Recursive force-remove detected",
    },
    {
        "pattern": r"\bcurl\b.*\|.*\bsh\b",
        "label": "remote-exec",
        "description": "Piping curl output into shell",
    },
    {
        "pattern": r"\bwget\b.*\|.*\bsh\b",
        "label": "remote-exec",
        "description": "Piping wget output into shell",
    },
    {
        "pattern": r"\bchmod\s+777\b",
        "label": "permission",
        "description": "World-writable chmod 777 detected",
    },
    {
        "pattern": r"\bdrop\s+table\b",
        "label": "database",
        "description": "SQL DROP TABLE in cron command",
    },
    {
        "pattern": r"\btruncate\b",
        "label": "database",
        "description": "SQL or file truncate command detected",
    },
    {
        "pattern": r"\b(?:password|passwd|secret|token)\s*=\s*\S+",
        "label": "secret",
        "description": "Hardcoded credential in command",
    },
]


def match_entry(
    entry: CrontabEntry,
    extra_patterns: Optional[List[dict]] = None,
) -> List[PatternMatch]:
    """Return all pattern matches for a single entry."""
    patterns = _BUILTIN_PATTERNS + (extra_patterns or [])
    results: List[PatternMatch] = []
    cmd = entry.command or ""
    for spec in patterns:
        if re.search(spec["pattern"], cmd, re.IGNORECASE):
            results.append(
                PatternMatch(
                    entry=entry,
                    pattern=spec["pattern"],
                    label=spec["label"],
                    description=spec["description"],
                )
            )
    return results


def match_entries(
    entries: List[CrontabEntry],
    extra_patterns: Optional[List[dict]] = None,
) -> List[PatternMatch]:
    """Return all pattern matches across a list of entries."""
    results: List[PatternMatch] = []
    for entry in entries:
        results.extend(match_entry(entry, extra_patterns=extra_patterns))
    return results
