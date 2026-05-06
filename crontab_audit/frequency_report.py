"""Formats frequency classification reports for crontab entries."""

from typing import List, Dict
from crontab_audit.parser import CrontabEntry
from crontab_audit.scheduler import classify_frequency


def group_by_frequency(entries: List[CrontabEntry]) -> Dict[str, List[CrontabEntry]]:
    """Group entries by their frequency classification."""
    groups: Dict[str, List[CrontabEntry]] = {}
    for entry in entries:
        label = classify_frequency(entry)
        groups.setdefault(label, []).append(entry)
    return groups


def format_frequency_group(label: str, entries: List[CrontabEntry]) -> str:
    """Format a single frequency group as a text block."""
    lines = [f"[{label.upper()}] ({len(entries)} entries)"]
    for e in entries:
        host = f"{e.host}: " if e.host else ""
        lines.append(f"  {host}{e.schedule_fields} -> {e.command}")
    return "\n".join(lines)


def format_frequency_report(entries: List[CrontabEntry], show_empty: bool = False) -> str:
    """Format a full frequency report across all classification buckets."""
    if not entries:
        return "No entries to report."

    order = ["minutely", "hourly", "daily", "weekly", "monthly", "other"]
    groups = group_by_frequency(entries)
    sections = []

    for label in order:
        if label in groups:
            sections.append(format_frequency_group(label, groups[label]))
        elif show_empty:
            sections.append(f"[{label.upper()}] (0 entries)")

    # Include any unexpected labels not in the standard order
    for label in groups:
        if label not in order:
            sections.append(format_frequency_group(label, groups[label]))

    return "\n\n".join(sections)


def format_frequency_summary(entries: List[CrontabEntry]) -> str:
    """Return a one-line summary of frequency distribution."""
    if not entries:
        return "Frequency summary: no entries."
    groups = group_by_frequency(entries)
    parts = [f"{label}={len(grp)}" for label, grp in sorted(groups.items())]
    return "Frequency summary: " + ", ".join(parts)
