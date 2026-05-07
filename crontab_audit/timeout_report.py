"""Formatting helpers for timeout/overlap-risk reports."""

from typing import List

from crontab_audit.timeout_checker import TimeoutIssue


def format_timeout_issues(issues: List[TimeoutIssue]) -> str:
    """Return a human-readable block listing all timeout issues."""
    if not issues:
        return "No timeout risk issues found."
    lines = ["Timeout Risk Issues:", "-" * 40]
    for issue in issues:
        lines.append(str(issue))
    return "\n".join(lines)


def format_timeout_by_severity(issues: List[TimeoutIssue]) -> str:
    """Group issues by severity and format each group."""
    if not issues:
        return "No timeout risk issues found."

    groups: dict = {}
    for issue in issues:
        groups.setdefault(issue.severity, []).append(issue)

    lines = []
    for severity in ("critical", "warning", "info"):
        group = groups.get(severity, [])
        if not group:
            continue
        lines.append(f"[{severity.upper()}] ({len(group)} issue(s))")
        for issue in group:
            host = issue.entry.host or "unknown"
            lines.append(f"  {host}: {issue.entry.command}")
            lines.append(f"    {issue.reason}")
    return "\n".join(lines)


def format_timeout_summary(issues: List[TimeoutIssue]) -> str:
    """Return a one-line summary of timeout risk findings."""
    if not issues:
        return "Timeout check passed: 0 issues."
    critical = sum(1 for i in issues if i.severity == "critical")
    warnings = sum(1 for i in issues if i.severity == "warning")
    parts = []
    if critical:
        parts.append(f"{critical} critical")
    if warnings:
        parts.append(f"{warnings} warning(s)")
    return f"Timeout risks detected: {', '.join(parts)} across {len(issues)} entr(ies)."
