"""Formatting helpers for filtered entry results."""

from __future__ import annotations

from typing import List

from crontab_audit.parser import CrontabEntry
from crontab_audit.entry_filter import EntryFilter


def format_filter_criteria(f: EntryFilter) -> str:
    parts = []
    if f.host:
        parts.append(f"host={f.host}")
    if f.user:
        parts.append(f"user={f.user}")
    if f.command_pattern:
        parts.append(f"command~={f.command_pattern}")
    if f.minute:
        parts.append(f"minute={f.minute}")
    if f.hour:
        parts.append(f"hour={f.hour}")
    if f.tags:
        parts.append(f"tags={','.join(f.tags)}")
    return "Filters: " + (" | ".join(parts) if parts else "(none)")


def format_filtered_entries(entries: List[CrontabEntry], f: EntryFilter) -> str:
    lines = [format_filter_criteria(f), ""]
    if not entries:
        lines.append("No entries matched the given criteria.")
        return "\n".join(lines)
    lines.append(f"{len(entries)} matching entr{'y' if len(entries) == 1 else 'ies'}:")
    for entry in entries:
        host = getattr(entry, "host", "unknown")
        schedule = " ".join(entry.schedule_fields)
        lines.append(f"  [{host}] {schedule}  {entry.command}")
    return "\n".join(lines)


def format_filter_summary(total: int, matched: int) -> str:
    pct = (matched / total * 100) if total > 0 else 0.0
    return f"Matched {matched}/{total} entries ({pct:.1f}%)"
