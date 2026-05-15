"""Formatting helpers for secret scanner results."""
from __future__ import annotations
from typing import List, Dict

from crontab_audit.secret_scanner import SecretIssue


def format_secret_issues(issues: List[SecretIssue]) -> str:
    if not issues:
        return "No secret issues found."
    lines = ["Secret Issues:", "-" * 40]
    for issue in issues:
        lines.append(str(issue))
    return "\n".join(lines)


def format_secrets_by_host(issues: List[SecretIssue]) -> str:
    if not issues:
        return "No secret issues found."
    grouped: Dict[str, List[SecretIssue]] = {}
    for issue in issues:
        host = issue.entry.host or "unknown"
        grouped.setdefault(host, []).append(issue)
    lines = []
    for host, host_issues in sorted(grouped.items()):
        lines.append(f"Host: {host} ({len(host_issues)} issue(s))")
        for issue in host_issues:
            lines.append(f"  {issue.reason}: {issue.matched_text}")
    return "\n".join(lines)


def format_secret_summary(issues: List[SecretIssue]) -> str:
    total = len(issues)
    if total == 0:
        return "Secret scan summary: 0 issues found."
    reasons: Dict[str, int] = {}
    for issue in issues:
        reasons[issue.reason] = reasons.get(issue.reason, 0) + 1
    lines = [f"Secret scan summary: {total} issue(s) found."]
    for reason, count in sorted(reasons.items(), key=lambda x: -x[1]):
        lines.append(f"  {reason}: {count}")
    return "\n".join(lines)
