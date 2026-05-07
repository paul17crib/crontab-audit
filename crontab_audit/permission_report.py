"""Formats permission check results for display."""

from typing import List, Dict
from crontab_audit.permission_checker import PermissionIssue


def format_permission_issues(issues: List[PermissionIssue]) -> str:
    if not issues:
        return "No permission issues found."
    lines = ["Permission Issues:", "-" * 40]
    for issue in issues:
        lines.append(str(issue))
    return "\n".join(lines)


def format_permission_by_severity(issues: List[PermissionIssue]) -> str:
    if not issues:
        return "No permission issues found."
    grouped: Dict[str, List[PermissionIssue]] = {}
    for issue in issues:
        grouped.setdefault(issue.severity, []).append(issue)
    lines = []
    for severity in ("critical", "warning", "info"):
        group = grouped.get(severity, [])
        if not group:
            continue
        lines.append(f"[{severity.upper()}] ({len(group)} issue(s)):")
        for issue in group:
            host = issue.entry.host or "unknown"
            lines.append(f"  {host}: {issue.entry.command!r}")
            lines.append(f"    → {issue.reason}")
    return "\n".join(lines)


def format_permission_summary(issues: List[PermissionIssue]) -> str:
    total = len(issues)
    criticals = sum(1 for i in issues if i.severity == "critical")
    warnings = sum(1 for i in issues if i.severity == "warning")
    infos = sum(1 for i in issues if i.severity == "info")
    lines = [
        f"Permission Check Summary:",
        f"  Total issues : {total}",
        f"  Critical     : {criticals}",
        f"  Warning      : {warnings}",
        f"  Info         : {infos}",
    ]
    return "\n".join(lines)
