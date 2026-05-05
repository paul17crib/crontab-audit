"""Formatting utilities for audit reports and host crontab summaries."""

from typing import List
from crontab_audit.loader import HostCrontab
from crontab_audit.reporter import AuditReport
from crontab_audit.scheduler import classify_frequency


def format_host_summary(host_crontab: HostCrontab, verbose: bool = False) -> str:
    """Return a formatted summary string for a single host's crontab."""
    lines = [f"Host: {host_crontab.hostname}"]
    lines.append(f"  Entries : {len(host_crontab.entries)}")
    lines.append(f"  Errors  : {len(host_crontab.parse_errors)}")

    if verbose and host_crontab.entries:
        lines.append("  Scheduled jobs:")
        for entry in host_crontab.entries:
            freq = classify_frequency(entry)
            lines.append(f"    [{freq:>10}]  {entry.command}")

    return "\n".join(lines)


def format_all_hosts(host_crontabs: List[HostCrontab], verbose: bool = False) -> str:
    """Return a combined formatted string for all hosts."""
    sections = [format_host_summary(hc, verbose=verbose) for hc in host_crontabs]
    return "\n\n".join(sections)


def format_report(report: AuditReport, verbose: bool = False) -> str:
    """Return a human-readable representation of a full audit report."""
    lines = ["=== Crontab Audit Report ==="]
    lines.append(report.summary())

    if verbose or report.has_issues():
        lines.append("")
        lines.append("--- Details ---")
        lines.append(report.detailed())

    return "\n".join(lines)


def format_parse_errors(host_crontab: HostCrontab) -> str:
    """Return a formatted list of parse errors for a host, or empty string if none."""
    if not host_crontab.parse_errors:
        return ""
    lines = [f"Parse errors for {host_crontab.hostname}:"]
    for err in host_crontab.parse_errors:
        lines.append(f"  - {err}")
    return "\n".join(lines)
