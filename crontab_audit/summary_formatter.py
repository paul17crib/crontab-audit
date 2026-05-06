"""Formats MultiHostSummary and HostSummaryStats for display."""

from typing import List
from crontab_audit.summarizer import MultiHostSummary, HostSummaryStats


_SEPARATOR = "-" * 60


def format_host_stats(stats: HostSummaryStats, verbose: bool = False) -> str:
    """Format a single host's summary stats as a readable string."""
    lines = [
        f"Host: {stats.hostname}",
        f"  Entries      : {stats.total_entries}",
        f"  Risky        : {stats.risky_count}",
        f"  Overlaps     : {stats.overlap_count}",
        f"  Parse Errors : {stats.parse_error_count}",
    ]
    if verbose and stats.risk_commands:
        lines.append("  Risky Commands:")
        for cmd in stats.risk_commands:
            lines.append(f"    - {cmd}")
    return "\n".join(lines)


def format_multi_host_summary(summary: MultiHostSummary, verbose: bool = False) -> str:
    """Format the full multi-host summary report."""
    lines = [
        "=" * 60,
        "CRONTAB AUDIT — MULTI-HOST SUMMARY",
        "=" * 60,
        f"Hosts Scanned  : {summary.total_hosts}",
        f"Total Entries  : {summary.total_entries}",
        f"Total Risky    : {summary.total_risky}",
        f"Total Overlaps : {summary.total_overlaps}",
        f"Total Parse Errors: {summary.total_parse_errors}",
    ]

    if summary.hosts_with_issues:
        lines.append("\nHosts With Issues:")
        for hostname in summary.hosts_with_issues:
            lines.append(f"  * {hostname}")
    else:
        lines.append("\nNo issues detected across all hosts.")

    if summary.host_stats:
        lines.append(f"\n{_SEPARATOR}")
        lines.append("Per-Host Breakdown:")
        lines.append(_SEPARATOR)
        for stats in summary.host_stats:
            lines.append(format_host_stats(stats, verbose=verbose))
            lines.append(_SEPARATOR)

    return "\n".join(lines)


def format_issues_only(summary: MultiHostSummary) -> str:
    """Return a compact listing of only hosts that have issues."""
    problematic = [
        s for s in summary.host_stats
        if s.risky_count > 0 or s.overlap_count > 0 or s.parse_error_count > 0
    ]
    if not problematic:
        return "No issues found across all hosts."

    lines = ["Hosts with issues:"]
    for stats in problematic:
        parts = []
        if stats.risky_count:
            parts.append(f"{stats.risky_count} risky")
        if stats.overlap_count:
            parts.append(f"{stats.overlap_count} overlapping")
        if stats.parse_error_count:
            parts.append(f"{stats.parse_error_count} parse errors")
        lines.append(f"  {stats.hostname}: {', '.join(parts)}")
    return "\n".join(lines)
