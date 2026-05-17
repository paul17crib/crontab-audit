"""Formatting helpers for entry search results."""
from __future__ import annotations

from typing import List

from crontab_audit.entry_search import SearchResult


def format_search_results(results: List[SearchResult], *, verbose: bool = False) -> str:
    """Return a human-readable block listing all search results."""
    if not results:
        return "No matching entries found."

    lines = [f"Found {len(results)} matching entr{'y' if len(results) == 1 else 'ies'}:", ""]
    for res in results:
        host = res.entry.host or "unknown"
        user_part = f" ({res.entry.user})" if res.entry.user else ""
        lines.append(f"  [{host}]{user_part} {res.snippet}")
        if verbose:
            lines.append(f"    schedule : {res.entry.schedule_fields}")
            lines.append(f"    matched  : {', '.join(res.matched_fields)}")
    return "\n".join(lines)


def format_search_summary(results: List[SearchResult]) -> str:
    """Return a one-line summary of a search result set."""
    if not results:
        return "Search returned 0 results."
    hosts = {res.entry.host for res in results if res.entry.host}
    return (
        f"Search returned {len(results)} result(s) "
        f"across {len(hosts)} host(s)."
    )


def format_results_by_host(results: List[SearchResult]) -> str:
    """Group and format search results by host."""
    if not results:
        return "No matching entries found."

    grouped: dict[str, List[SearchResult]] = {}
    for res in results:
        key = res.entry.host or "unknown"
        grouped.setdefault(key, []).append(res)

    lines: List[str] = []
    for host in sorted(grouped):
        group = grouped[host]
        lines.append(f"{host} ({len(group)} match{'es' if len(group) != 1 else ''}):")
        for res in group:
            lines.append(f"  {res.snippet}")
        lines.append("")
    return "\n".join(lines).rstrip()
