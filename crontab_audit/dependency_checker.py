"""Detects crontab entries that may depend on each other via shared files or commands."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple
import re

from crontab_audit.parser import CrontabEntry


@dataclass
class DependencyHint:
    entry_a: CrontabEntry
    entry_b: CrontabEntry
    shared_token: str
    reason: str

    def __str__(self) -> str:
        return (
            f"[{self.entry_a.host}] '{self.entry_a.command}' <-> "
            f"[{self.entry_b.host}] '{self.entry_b.command}' "
            f"(shared: {self.shared_token!r} — {self.reason})"
        )


_PATH_RE = re.compile(r"(/[\w./-]{3,})")
_ENV_RE = re.compile(r"\$(\w+)")


def _extract_tokens(command: str) -> set:
    """Extract file paths and env vars from a command string."""
    tokens: set = set()
    tokens.update(_PATH_RE.findall(command))
    tokens.update(f"${v}" for v in _ENV_RE.findall(command))
    return tokens


def find_dependencies(
    entries: List[CrontabEntry],
    min_token_length: int = 4,
) -> List[DependencyHint]:
    """Return pairs of entries that share file paths or env vars in their commands."""
    hints: List[DependencyHint] = []
    token_map: dict = {}  # token -> list of entries

    for entry in entries:
        for token in _extract_tokens(entry.command):
            if len(token) < min_token_length:
                continue
            token_map.setdefault(token, []).append(entry)

    seen: set = set()
    for token, matching in token_map.items():
        for i in range(len(matching)):
            for j in range(i + 1, len(matching)):
                a, b = matching[i], matching[j]
                key = (id(a), id(b), token)
                if key in seen:
                    continue
                seen.add(key)
                reason = "shared file path" if token.startswith("/") else "shared env var"
                hints.append(DependencyHint(a, b, token, reason))

    return hints
