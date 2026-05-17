"""Formatting helpers for entry grouper output."""

from typing import Dict, List
from crontab_audit.entry_grouper import EntryGroup


def format_group_header(key: str, count: int) -> str:
    return f"[{key}]  ({count} {'entry' if count == 1 else 'entries'})"


def format_group(group: EntryGroup, verbose: bool = False) -> str:
    lines = [format_group_header(group.key, len(group))]
    if verbose:
        for entry in group.entries:
            host_tag = f"[{entry.host}] " if entry.host else ""
            schedule = " ".join(entry.schedule_fields)
            lines.append(f"  {host_tag}{schedule}  {entry.command}")
    return "\n".join(lines)


def format_groups(groups: Dict[str, EntryGroup], verbose: bool = False) -> str:
    if not groups:
        return "No entries to group."
    sections = [format_group(g, verbose=verbose) for g in groups.values()]
    return "\n\n".join(sections)


def format_group_summary(groups: Dict[str, EntryGroup]) -> str:
    if not groups:
        return "No groups found."
    total_entries = sum(len(g) for g in groups.values())
    lines = [f"Groups: {len(groups)}  Total entries: {total_entries}"]
    for key, group in groups.items():
        lines.append(f"  {key}: {len(group)}")
    return "\n".join(lines)


def format_largest_groups(groups: Dict[str, EntryGroup], top_n: int = 5) -> str:
    ranked = sorted(groups.values(), key=lambda g: len(g), reverse=True)[:top_n]
    if not ranked:
        return "No groups."
    lines = [f"Top {top_n} groups by entry count:"]
    for group in ranked:
        lines.append(f"  {group.key}: {len(group)}")
    return "\n".join(lines)
