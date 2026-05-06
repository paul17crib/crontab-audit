"""Formatting helpers for command statistics reports."""

from __future__ import annotations

from typing import Dict, List

from crontab_audit.command_stats import CommandStats, build_command_stats, top_commands
from crontab_audit.parser import CrontabEntry


def format_command_stats(stats: Dict[str, CommandStats]) -> str:
    """Format a full command stats mapping as a human-readable table."""
    if not stats:
        return "No commands found."
    lines = [f"{'Command':<30} {'Count':>6}  Hosts"]
    lines.append("-" * 60)
    for key in sorted(stats, key=lambda k: -stats[k].count):
        s = stats[key]
        hosts = ", ".join(sorted(set(h for h in s.hosts if h)))
        lines.append(f"{key:<30} {s.count:>6}  {hosts}")
    return "\n".join(lines)


def format_top_commands(entries: List[CrontabEntry], n: int = 10) -> str:
    """Format the top-n commands as a ranked list."""
    top = top_commands(entries, n)
    if not top:
        return "No commands found."
    lines = [f"Top {n} commands by frequency:", ""]
    for rank, s in enumerate(top, start=1):
        hosts = ", ".join(sorted(set(h for h in s.hosts if h))) or "unknown"
        lines.append(f"  {rank:>2}. {s.command:<28} x{s.count}  ({hosts})")
    return "\n".join(lines)


def format_commands_per_host(entries: List[CrontabEntry]) -> str:
    """Format a per-host breakdown of command counts."""
    stats = build_command_stats(entries)
    host_map: Dict[str, int] = {}
    for s in stats.values():
        for host in s.hosts:
            host_map[host] = host_map.get(host, 0) + 1
    if not host_map:
        return "No entries."
    lines = ["Commands per host:", ""]
    for host in sorted(host_map):
        lines.append(f"  {host or 'unknown':<30} {host_map[host]} command(s)")
    return "\n".join(lines)
