"""Formats anomaly detection results for display."""
from typing import List
from crontab_audit.anomaly_detector import AnomalyIssue


def format_anomaly_issues(issues: List[AnomalyIssue]) -> str:
    if not issues:
        return "No anomalies detected."
    lines = ["Anomaly Report", "=" * 40]
    for issue in issues:
        lines.append(str(issue))
    return "\n".join(lines)


def format_anomalies_by_severity(issues: List[AnomalyIssue]) -> str:
    if not issues:
        return "No anomalies detected."
    grouped: dict = {"high": [], "medium": [], "low": []}
    for issue in issues:
        grouped.setdefault(issue.severity, []).append(issue)
    lines = ["Anomalies by Severity", "=" * 40]
    for severity in ("high", "medium", "low"):
        bucket = grouped.get(severity, [])
        if bucket:
            lines.append(f"\n[{severity.upper()}] ({len(bucket)} issue(s))")
            for issue in bucket:
                host = issue.entry.host or "unknown"
                lines.append(f"  {host}: {issue.entry.command!r} — {issue.reason}")
    return "\n".join(lines)


def format_anomaly_summary(issues: List[AnomalyIssue]) -> str:
    total = len(issues)
    high = sum(1 for i in issues if i.severity == "high")
    medium = sum(1 for i in issues if i.severity == "medium")
    low = sum(1 for i in issues if i.severity == "low")
    return (
        f"Anomaly Summary: {total} total "
        f"(high={high}, medium={medium}, low={low})"
    )
