"""Formatting helpers for annotated crontab entries."""
from typing import List, Optional

from crontab_audit.entry_annotator import AnnotatedEntry


def format_annotated_entry(ann: AnnotatedEntry, verbose: bool = False) -> str:
    host = ann.entry.host or "unknown"
    cmd = ann.entry.command
    freq = ann.frequency_label
    line = f"  [{host}] {cmd}  ({freq})"
    if ann.risk_flags:
        line += f"  !! {', '.join(ann.risk_flags)}"
    if verbose and ann.notes:
        line += f"  -- {'; '.join(ann.notes)}"
    return line


def format_annotated_report(
    annotated: List[AnnotatedEntry],
    verbose: bool = False,
    title: Optional[str] = None,
) -> str:
    if not annotated:
        return "No annotated entries to display."
    lines: List[str] = []
    if title:
        lines.append(title)
        lines.append("-" * len(title))
    for ann in annotated:
        lines.append(format_annotated_entry(ann, verbose=verbose))
    return "\n".join(lines)


def format_annotation_summary(annotated: List[AnnotatedEntry]) -> str:
    total = len(annotated)
    risky = sum(1 for a in annotated if a.is_risky)
    freq_counts: dict = {}
    for ann in annotated:
        freq_counts[ann.frequency_label] = freq_counts.get(ann.frequency_label, 0) + 1

    lines = [
        f"Annotation Summary",
        f"  Total entries : {total}",
        f"  Risky entries : {risky}",
        f"  Frequency breakdown:",
    ]
    for label, count in sorted(freq_counts.items()):
        lines.append(f"    {label:<15} {count}")
    return "\n".join(lines)


def format_risky_only(annotated: List[AnnotatedEntry]) -> str:
    risky = [a for a in annotated if a.is_risky]
    if not risky:
        return "No risky entries found."
    return format_annotated_report(risky, verbose=True, title="Risky Entries")
