"""Formats classification label reports for crontab entries."""

from typing import List, Dict
from crontab_audit.label_classifier import LabeledEntry, group_by_label


def format_labeled_entry(item: LabeledEntry) -> str:
    host = getattr(item.entry, "host", "unknown")
    labels = ", ".join(item.labels) if item.labels else "unknown"
    return f"  [{labels}] {host}: {item.entry.command}"


def format_label_group(label: str, items: List[LabeledEntry]) -> str:
    lines = [f"=== {label.upper()} ({len(items)}) ==="]
    for item in sorted(items, key=lambda i: getattr(i.entry, "host", "")):
        lines.append(format_labeled_entry(item))
    return "\n".join(lines)


def format_label_report(labeled: List[LabeledEntry]) -> str:
    """Full report grouped by label."""
    if not labeled:
        return "No entries to classify."
    groups = group_by_label(labeled)
    sections = [
        format_label_group(label, items)
        for label, items in sorted(groups.items())
    ]
    return "\n\n".join(sections)


def format_label_summary(labeled: List[LabeledEntry]) -> str:
    """One-line count per label."""
    if not labeled:
        return "No entries classified."
    groups = group_by_label(labeled)
    lines = ["Label Classification Summary:", "-" * 32]
    for label, items in sorted(groups.items()):
        lines.append(f"  {label:<20} {len(items):>4} entries")
    lines.append("-" * 32)
    lines.append(f"  {'TOTAL':<20} {len(labeled):>4} entries")
    return "\n".join(lines)


def format_unknown_entries(labeled: List[LabeledEntry]) -> str:
    """List entries that could not be classified."""
    unknown = [item for item in labeled if not item.labels]
    if not unknown:
        return "All entries were successfully classified."
    lines = [f"Unclassified entries ({len(unknown)}):"]
    for item in unknown:
        host = getattr(item.entry, "host", "unknown")
        lines.append(f"  {host}: {item.entry.command}")
    return "\n".join(lines)
