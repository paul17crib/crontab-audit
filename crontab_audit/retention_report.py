"""Formatting helpers for retention policy results."""

from __future__ import annotations

from typing import List

from crontab_audit.retention import RetentionIssue


def format_retention_issues(issues: List[RetentionIssue]) -> str:
    """Return a human-readable block listing all retention issues."""
    if not issues:
        return "No retention issues found."

    lines = [f"Retention Issues ({len(issues)} found):", "-" * 40]
    for issue in issues:
        lines.append(str(issue))
    return "\n".join(lines)


def format_retention_by_host(issues: List[RetentionIssue]) -> str:
    """Group and format retention issues by host."""
    if not issues:
        return "No retention issues found."

    by_host: dict[str, List[RetentionIssue]] = {}
    for issue in issues:
        host = issue.entry.host or "unknown"
        by_host.setdefault(host, []).append(issue)

    lines: List[str] = []
    for host, host_issues in sorted(by_host.items()):
        lines.append(f"Host: {host} ({len(host_issues)} issue(s))")
        for issue in host_issues:
            lines.append(f"  - {issue.reason}")
            lines.append(f"    command: {issue.entry.command}")
        lines.append("")

    return "\n".join(lines).rstrip()


def format_retention_summary(issues: List[RetentionIssue]) -> str:
    """One-line summary suitable for CI output or dashboards."""
    if not issues:
        return "retention: OK"
    hosts = {i.entry.host or 'unknown' for i in issues}
    return (
        f"retention: {len(issues)} issue(s) across "
        f"{len(hosts)} host(s)"
    )
