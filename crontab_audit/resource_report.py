"""Formatting helpers for resource monitor output."""
from __future__ import annotations
from typing import List, Dict
from crontab_audit.resource_monitor import ResourceIssue


def format_resource_issues(issues: List[ResourceIssue]) -> str:
    if not issues:
        return "No resource contention issues found."
    lines = ["Resource Contention Issues:", ""]
    for issue in issues:
        lines.append(f"  {issue}")
    return "\n".join(lines)


def format_resource_by_severity(issues: List[ResourceIssue]) -> str:
    grouped: Dict[str, List[ResourceIssue]] = {"high": [], "medium": [], "low": []}
    for issue in issues:
        grouped.setdefault(issue.severity, []).append(issue)

    lines = []
    for severity in ("high", "medium", "low"):
        bucket = grouped[severity]
        if not bucket:
            continue
        lines.append(f"[{severity.upper()}] — {len(bucket)} issue(s):")
        for issue in bucket:
            host = issue.entry.host or "unknown"
            lines.append(f"  {host}: {issue.entry.command} — {issue.reason}")
        lines.append("")
    return "\n".join(lines).rstrip()


def format_resource_summary(issues: List[ResourceIssue]) -> str:
    total = len(issues)
    if total == 0:
        return "Resource summary: 0 issues detected."
    high = sum(1 for i in issues if i.severity == "high")
    medium = sum(1 for i in issues if i.severity == "medium")
    low = sum(1 for i in issues if i.severity == "low")
    return (
        f"Resource summary: {total} issue(s) — "
        f"{high} high, {medium} medium, {low} low"
    )
