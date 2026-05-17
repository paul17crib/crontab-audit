"""Formatting helpers for entry lint results."""
from typing import List, Dict
from crontab_audit.entry_linter import LintIssue

_SEVERITY_ORDER = {"error": 0, "warning": 1, "info": 2}


def format_lint_issues(issues: List[LintIssue]) -> str:
    """Format a flat list of lint issues."""
    if not issues:
        return "No lint issues found."
    lines = ["Lint Issues:", "-" * 40]
    for issue in sorted(issues, key=lambda i: _SEVERITY_ORDER.get(i.severity, 99)):
        lines.append(str(issue))
    return "\n".join(lines)


def format_lint_by_severity(issues: List[LintIssue]) -> str:
    """Group and format lint issues by severity."""
    if not issues:
        return "No lint issues found."
    groups: Dict[str, List[LintIssue]] = {"error": [], "warning": [], "info": []}
    for issue in issues:
        groups.setdefault(issue.severity, []).append(issue)
    lines = []
    for severity in ("error", "warning", "info"):
        bucket = groups[severity]
        if not bucket:
            continue
        lines.append(f"\n{severity.upper()}S ({len(bucket)})")
        lines.append("-" * 30)
        for issue in bucket:
            lines.append(f"  [{issue.code}] {issue.message}")
            lines.append(f"    host={issue.entry.host or 'unknown'}  cmd={issue.entry.command}")
    return "\n".join(lines).strip()


def format_lint_summary(issues: List[LintIssue]) -> str:
    """One-line summary of lint results."""
    errors = sum(1 for i in issues if i.severity == "error")
    warnings = sum(1 for i in issues if i.severity == "warning")
    infos = sum(1 for i in issues if i.severity == "info")
    total = len(issues)
    if total == 0:
        return "Lint summary: 0 issues — all entries look clean."
    return (
        f"Lint summary: {total} issue(s) — "
        f"{errors} error(s), {warnings} warning(s), {infos} info(s)"
    )


def format_lint_by_code(issues: List[LintIssue]) -> str:
    """Group lint issues by rule code."""
    if not issues:
        return "No lint issues found."
    groups: Dict[str, List[LintIssue]] = {}
    for issue in issues:
        groups.setdefault(issue.code, []).append(issue)
    lines = ["Lint Issues by Code:", "=" * 40]
    for code in sorted(groups):
        bucket = groups[code]
        lines.append(f"\n{code}  ({len(bucket)} occurrence(s))")
        for issue in bucket:
            host = issue.entry.host or "unknown"
            lines.append(f"  {host}: {issue.message}")
    return "\n".join(lines)
