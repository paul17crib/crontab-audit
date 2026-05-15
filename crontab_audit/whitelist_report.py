"""Formatting helpers for whitelist audit output."""
from __future__ import annotations

from typing import List

from crontab_audit.parser import CrontabEntry
from crontab_audit.whitelist import Whitelist, WhitelistEntry


def format_whitelist_entries(entries: List[WhitelistEntry]) -> str:
    if not entries:
        return "Whitelist is empty."
    lines = ["Whitelist entries:", ""]
    for i, e in enumerate(entries, 1):
        parts = []
        if e.host:
            parts.append(f"host={e.host}")
        if e.schedule_exact:
            parts.append(f"schedule={e.schedule_exact!r}")
        if e.command_contains:
            parts.append(f"command contains {e.command_contains!r}")
        reason = f"  # {e.reason}" if e.reason else ""
        lines.append(f"  {i}. {', '.join(parts)}{reason}")
    return "\n".join(lines)


def format_whitelisted_entries(
    entries: List[CrontabEntry], whitelist: Whitelist
) -> str:
    matched = [e for e in entries if whitelist.is_whitelisted(e)]
    if not matched:
        return "No entries matched the whitelist."
    lines = [f"Whitelisted entries ({len(matched)} suppressed):", ""]
    for e in matched:
        host_tag = f"[{e.host}] " if e.host else ""
        lines.append(f"  {host_tag}{e} -> {e.command}")
    return "\n".join(lines)


def format_whitelist_summary(
    total: int, suppressed: int
) -> str:
    active = total - suppressed
    return (
        f"Whitelist summary: {total} entries total, "
        f"{suppressed} suppressed, {active} active."
    )
