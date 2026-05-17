"""Full-text and field-specific search across crontab entries."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from crontab_audit.parser import CrontabEntry


@dataclass
class SearchResult:
    entry: CrontabEntry
    matched_fields: List[str]
    snippet: str

    def __str__(self) -> str:
        host = self.entry.host or "unknown"
        return f"[{host}] {self.entry.command!r} (matched: {', '.join(self.matched_fields)})"


def _highlight(text: str, pattern: re.Pattern) -> str:
    """Return text with matched portions wrapped in angle brackets."""
    return pattern.sub(lambda m: f"<{m.group()}>", text)


def search_entries(
    entries: List[CrontabEntry],
    query: str,
    *,
    case_sensitive: bool = False,
    fields: Optional[List[str]] = None,
) -> List[SearchResult]:
    """Search entries for *query* across selected fields.

    Parameters
    ----------
    entries:
        Flat list of :class:`CrontabEntry` objects to search.
    query:
        The search string (treated as a regular expression).
    case_sensitive:
        When *False* (default) matching ignores case.
    fields:
        Subset of ``["command", "host", "user", "schedule"]`` to search.
        Defaults to all fields.
    """
    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        pattern = re.compile(query, flags)
    except re.error as exc:
        raise ValueError(f"Invalid search query {query!r}: {exc}") from exc

    allowed = set(fields) if fields else {"command", "host", "user", "schedule"}
    results: List[SearchResult] = []

    for entry in entries:
        candidates: dict[str, str] = {}
        if "command" in allowed:
            candidates["command"] = entry.command
        if "host" in allowed and entry.host:
            candidates["host"] = entry.host
        if "user" in allowed and entry.user:
            candidates["user"] = entry.user
        if "schedule" in allowed:
            candidates["schedule"] = str(entry)

        matched: List[str] = []
        snippet_source = entry.command
        for fname, fval in candidates.items():
            if pattern.search(fval):
                matched.append(fname)

        if matched:
            snippet = _highlight(snippet_source, pattern)
            results.append(SearchResult(entry=entry, matched_fields=matched, snippet=snippet))

    return results


def search_by_command(entries: List[CrontabEntry], query: str) -> List[SearchResult]:
    """Convenience wrapper that only searches the command field."""
    return search_entries(entries, query, fields=["command"])


def search_by_host(entries: List[CrontabEntry], host: str) -> List[SearchResult]:
    """Convenience wrapper that only searches the host field."""
    return search_entries(entries, re.escape(host), fields=["host"])
