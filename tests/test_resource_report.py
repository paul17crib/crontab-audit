"""Tests for crontab_audit.resource_report."""
import pytest
from crontab_audit.parser import CrontabEntry
from crontab_audit.resource_monitor import ResourceIssue
from crontab_audit.resource_report import (
    format_resource_issues,
    format_resource_by_severity,
    format_resource_summary,
)


def make_entry(command="rsync /a /b", host="h1"):
    return CrontabEntry(
        minute="*", hour="*", dom="*", month="*", dow="*",
        command=command, host=host,
    )


def make_issue(command="rsync /a /b", host="h1", severity="high", reason="test"):
    return ResourceIssue(
        entry=make_entry(command=command, host=host),
        reason=reason,
        severity=severity,
    )


def test_format_resource_issues_empty():
    result = format_resource_issues([])
    assert "No resource" in result


def test_format_resource_issues_includes_entry():
    issues = [make_issue(command="rsync /a /b", host="web1")]
    result = format_resource_issues(issues)
    assert "web1" in result
    assert "rsync" in result


def test_format_resource_issues_header_present():
    issues = [make_issue()]
    result = format_resource_issues(issues)
    assert "Resource Contention Issues" in result


def test_format_resource_by_severity_groups_correctly():
    issues = [
        make_issue(severity="high", reason="r1"),
        make_issue(severity="low", reason="r2"),
        make_issue(severity="medium", reason="r3"),
    ]
    result = format_resource_by_severity(issues)
    assert "HIGH" in result
    assert "MEDIUM" in result
    assert "LOW" in result


def test_format_resource_by_severity_empty_severity_omitted():
    issues = [make_issue(severity="high")]
    result = format_resource_by_severity(issues)
    assert "MEDIUM" not in result
    assert "LOW" not in result


def test_format_resource_summary_no_issues():
    result = format_resource_summary([])
    assert "0 issues" in result


def test_format_resource_summary_counts():
    issues = [
        make_issue(severity="high"),
        make_issue(severity="high"),
        make_issue(severity="medium"),
        make_issue(severity="low"),
    ]
    result = format_resource_summary(issues)
    assert "4 issue" in result
    assert "2 high" in result
    assert "1 medium" in result
    assert "1 low" in result
