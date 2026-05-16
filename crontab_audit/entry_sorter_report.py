"""Format sorted crontab entries for display."""
from __future__ import annotations
from typing import List
from crontab_audit.entry_sorter import SortedEntries
from crontab_audit.parser import CrontabEntry


def _entry_line(entry: CrontabEntry) -> str:
    schedule = " ".join(entry.schedule_fields)
    host = entry.host or "(unknown)"
    user = entry.user or ""
    user_part = f" [{user}]" if user else ""
    return f"  {host}{user_part}  {schedule}  {entry.command}"


def format_sorted_entries(result: SortedEntries, max_rows: int = 0) -> str:
    """Return a formatted table of sorted entries."""
    direction = "descending" if result.reverse else "ascending"
    lines: List[str] = [
        f"Sorted by: {result.sort_key} ({direction})",
        f"Total entries: {len(result.entries)}",
        "-" * 60,
    ]
    entries = result.entries
    if max_rows and max_rows < len(entries):
        entries = entries[:max_rows]
        truncated = True
    else:
        truncated = False
    for entry in entries:
        lines.append(_entry_line(entry))
    if truncated:
        lines.append(f"  ... (showing {max_rows} of {len(result.entries)})")
    return "\n".join(lines)


def format_sort_summary(result: SortedEntries) -> str:
    """Return a one-line summary of the sort operation."""
    direction = "desc" if result.reverse else "asc"
    return (
        f"{len(result.entries)} entr{'y' if len(result.entries) == 1 else 'ies'} "
        f"sorted by '{result.sort_key}' ({direction})"
    )


def format_grouped_by_key(result: SortedEntries) -> str:
    """Group sorted entries by their sort key value and format as sections."""
    from crontab_audit.entry_sorter import _SORT_KEYS
    key_fn = _SORT_KEYS.get(result.sort_key)
    if key_fn is None:
        return format_sorted_entries(result)
    groups: dict = {}
    for entry in result.entries:
        k = str(key_fn(entry))
        groups.setdefault(k, []).append(entry)
    lines: List[str] = [f"Grouped by: {result.sort_key}", "=" * 60]
    for group_key, group_entries in groups.items():
        lines.append(f"[{group_key}] ({len(group_entries)} entries)")
        for e in group_entries:
            lines.append(_entry_line(e))
        lines.append("")
    return "\n".join(lines).rstrip()
