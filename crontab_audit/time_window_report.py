"""Format time-window match results for human-readable output."""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from crontab_audit.time_window import TimeWindow, WindowMatch


def format_window_matches(matches: List[WindowMatch]) -> str:
    """Return a plain-text report grouped by window name."""
    if not matches:
        return "No entries matched any time window."

    grouped: Dict[str, List[WindowMatch]] = defaultdict(list)
    for m in matches:
        grouped[m.window.name].append(m)

    lines: List[str] = []
    for window_name, wmatches in sorted(grouped.items()):
        lines.append(f"Window: {window_name} ({len(wmatches)} entr{'y' if len(wmatches)==1 else 'ies'})")
        for m in wmatches:
            host = getattr(m.entry, 'host', 'unknown')
            schedule = " ".join(m.entry.schedule_fields)
            lines.append(f"  [{host}] {schedule}  {m.entry.command}")
        lines.append("")
    return "\n".join(lines).rstrip()


def format_window_summary(matches: List[WindowMatch]) -> str:
    """Return a one-line-per-window count summary."""
    if not matches:
        return "No window matches found."

    counts: Dict[str, int] = defaultdict(int)
    for m in matches:
        counts[m.window.name] += 1

    lines = ["Time-window summary:"]
    for name, count in sorted(counts.items()):
        lines.append(f"  {name}: {count}")
    return "\n".join(lines)


def format_off_hours_warnings(matches: List[WindowMatch]) -> str:
    """Highlight entries that run exclusively during off-hours (potential concern)."""
    off = [m for m in matches if m.window.name == "off-hours"]
    if not off:
        return "No off-hours entries detected."
    lines = [f"Off-hours entries ({len(off)}):"]
    for m in off:
        host = getattr(m.entry, 'host', 'unknown')
        lines.append(f"  [{host}] {m.entry.command}")
    return "\n".join(lines)
