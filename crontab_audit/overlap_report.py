"""Formatting utilities for overlap detection results."""

from typing import List
from crontab_audit.overlap import OverlapResult


def format_overlap_pair(result: OverlapResult) -> str:
    """Format a single overlap result as a human-readable string."""
    a = result.entry_a
    b = result.entry_b
    host_a = getattr(a, 'hostname', 'unknown')
    host_b = getattr(b, 'hostname', 'unknown')

    if host_a == host_b:
        host_label = f"[{host_a}]"
    else:
        host_label = f"[{host_a}] vs [{host_b}]"

    return (
        f"OVERLAP {host_label}\n"
        f"  Entry A: {a.schedule_fields} {a.command}\n"
        f"  Entry B: {b.schedule_fields} {b.command}"
    )


def format_overlap_report(results: List[OverlapResult], verbose: bool = False) -> str:
    """Format a full overlap report from a list of OverlapResult objects."""
    if not results:
        return "No overlapping schedules detected."

    lines = [f"Overlapping schedules detected: {len(results)} pair(s)\n"]
    for result in results:
        lines.append(format_overlap_pair(result))
        if verbose and result.overlap_minutes:
            lines.append(f"  Overlapping minutes: {sorted(result.overlap_minutes)[:10]}{'...' if len(result.overlap_minutes) > 10 else ''}")
        lines.append("")

    return "\n".join(lines).rstrip()


def format_overlap_summary(results: List[OverlapResult]) -> str:
    """Return a brief one-line summary of overlap findings."""
    if not results:
        return "Overlaps: none"
    hosts = set()
    for r in results:
        hosts.add(getattr(r.entry_a, 'hostname', 'unknown'))
        hosts.add(getattr(r.entry_b, 'hostname', 'unknown'))
    return f"Overlaps: {len(results)} pair(s) across {len(hosts)} host(s)"


def format_overlaps_by_host(results: List[OverlapResult]) -> str:
    """Group and format overlap results by host."""
    if not results:
        return "No overlapping schedules detected."

    by_host: dict = {}
    for r in results:
        host = getattr(r.entry_a, 'hostname', 'unknown')
        by_host.setdefault(host, []).append(r)

    lines = []
    for host, host_results in sorted(by_host.items()):
        lines.append(f"Host: {host} ({len(host_results)} overlap(s))")
        for r in host_results:
            lines.append(f"  - {r.entry_a.schedule_fields} {r.entry_a.command}")
            lines.append(f"    {r.entry_b.schedule_fields} {r.entry_b.command}")
        lines.append("")

    return "\n".join(lines).rstrip()
