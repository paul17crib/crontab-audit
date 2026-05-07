"""Tests for anomaly_report module."""
from crontab_audit.parser import CrontabEntry
from crontab_audit.anomaly_detector import AnomalyIssue
from crontab_audit.anomaly_report import (
    format_anomaly_issues,
    format_anomalies_by_severity,
    format_anomaly_summary,
)


def make_entry(command="echo test", host="host1"):
    return CrontabEntry(
        schedule_fields=["7", "*", "*", "*", "*"],
        command=command,
        host=host,
        raw_line=f"7 * * * * {command}",
    )


def make_issue(reason="Unusual minute", severity="medium", host="host1", command="echo hi"):
    return AnomalyIssue(
        entry=make_entry(command=command, host=host),
        reason=reason,
        severity=severity,
    )


def test_format_anomaly_issues_empty():
    result = format_anomaly_issues([])
    assert "No anomalies" in result


def test_format_anomaly_issues_includes_reason():
    issues = [make_issue(reason="Unusual minute value: 7")]
    result = format_anomaly_issues(issues)
    assert "Unusual minute value: 7" in result


def test_format_anomaly_issues_includes_host():
    issues = [make_issue(host="db-server")]
    result = format_anomaly_issues(issues)
    assert "db-server" in result


def test_format_anomalies_by_severity_empty():
    result = format_anomalies_by_severity([])
    assert "No anomalies" in result


def test_format_anomalies_by_severity_groups_correctly():
    issues = [
        make_issue(severity="high", reason="Critical issue"),
        make_issue(severity="low", reason="Minor issue"),
    ]
    result = format_anomalies_by_severity(issues)
    assert "HIGH" in result
    assert "LOW" in result
    assert "Critical issue" in result
    assert "Minor issue" in result


def test_format_anomaly_summary_counts():
    issues = [
        make_issue(severity="high"),
        make_issue(severity="medium"),
        make_issue(severity="medium"),
        make_issue(severity="low"),
    ]
    result = format_anomaly_summary(issues)
    assert "4 total" in result
    assert "high=1" in result
    assert "medium=2" in result
    assert "low=1" in result


def test_format_anomaly_summary_empty():
    result = format_anomaly_summary([])
    assert "0 total" in result
