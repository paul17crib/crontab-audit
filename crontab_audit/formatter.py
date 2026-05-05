"""Formats loader results and audit reports for human-readable output."""

from __future__ import annotations

from typing import Dict, Iterable

from crontab_audit.loader import HostCrontab
from crontab_audit.reporter import AuditReport


SEPARATOR = "-" * 60


def format_host_summary(host_crontab: HostCrontab) -> str:
    """Return a short summary string for one host's crontab."""
    lines = [
        f"Host : {host_crontab.hostname}",
        f"  Entries     : {len(host_crontab.entries)}",
        f"  Parse errors: {len(host_crontab.parse_errors)}",
    ]
    if host_crontab.parse_errors:
        for err in host_crontab.parse_errors:
            lines.append(f"    ! {err}")
    return "\n".join(lines)


def format_all_hosts(
    hosts: Dict[str, HostCrontab],
    verbose: bool = False,
) -> str:
    """Return a formatted string for all hosts."""
    sections = []
    for hostname in sorted(hosts):
        host_crontab = hosts[hostname]
        sections.append(format_host_summary(host_crontab))
        if verbose:
            for entry in host_crontab.entries:
                sections.append(f"    {entry}")
    return ("\n" + SEPARATOR + "\n").join(sections)


def format_report(report: AuditReport, verbose: bool = False) -> str:
    """Render an AuditReport as a human-readable string."""
    lines = [SEPARATOR, "CRONTAB AUDIT REPORT", SEPARATOR]
    if verbose:
        lines.append(report.detailed())
    else:
        lines.append(report.summary())
    lines.append(SEPARATOR)
    if report.has_issues():
        lines.append("STATUS: ISSUES FOUND")
    else:
        lines.append("STATUS: OK")
    return "\n".join(lines)


def format_parse_errors(hosts: Iterable[HostCrontab]) -> str:
    """Return a consolidated list of all parse errors across hosts."""
    all_errors = []
    for host in hosts:
        for err in host.parse_errors:
            all_errors.append(f"[{host.hostname}] {err}")
    if not all_errors:
        return "No parse errors found."
    return "Parse errors:\n" + "\n".join(f"  {e}" for e in all_errors)
