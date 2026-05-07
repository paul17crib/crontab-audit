"""Tests for permission_checker and permission_report."""

import pytest
from crontab_audit.parser import CrontabEntry
from crontab_audit.permission_checker import (
    check_permissions,
    _check_setuid,
    _check_world_writable,
    _check_sensitive_paths,
    PermissionIssue,
)
from crontab_audit.permission_report import (
    format_permission_issues,
    format_permission_by_severity,
    format_permission_summary,
)


def make_entry(command, host="host1", user=None):
    return CrontabEntry(
        minute="0",
        hour="1",
        dom="*",
        month="*",
        dow="*",
        command=command,
        host=host,
        user=user,
        raw=f"0 1 * * * {command}",
    )


def test_check_setuid_sudo():
    entry = make_entry("sudo /usr/bin/backup.sh")
    issues = _check_setuid(entry)
    assert len(issues) == 1
    assert issues[0].severity == "critical"
    assert "sudo" in issues[0].reason


def test_check_setuid_chmod():
    entry = make_entry("chmod 777 /var/data")
    issues = _check_setuid(entry)
    assert len(issues) == 1
    assert "chmod" in issues[0].reason


def test_check_setuid_safe_command():
    entry = make_entry("/usr/bin/python3 /opt/report.py")
    issues = _check_setuid(entry)
    assert issues == []


def test_check_world_writable_tmp():
    entry = make_entry("/bin/sh /tmp/run.sh")
    issues = _check_world_writable(entry)
    assert len(issues) == 1
    assert issues[0].severity == "warning"
    assert "/tmp/" in issues[0].reason


def test_check_world_writable_safe_path():
    entry = make_entry("/usr/local/bin/cleanup.sh")
    issues = _check_world_writable(entry)
    assert issues == []


def test_check_sensitive_paths_shadow():
    entry = make_entry("cat /etc/shadow")
    issues = _check_sensitive_paths(entry)
    assert any("/etc/shadow" in i.reason for i in issues)
    assert all(i.severity == "critical" for i in issues)


def test_check_sensitive_paths_safe():
    entry = make_entry("/usr/bin/backup.sh /home/user/data")
    issues = _check_sensitive_paths(entry)
    assert issues == []


def test_check_permissions_aggregates_all():
    entries = [
        make_entry("sudo chmod 777 /tmp/x"),
        make_entry("/bin/safe_script.sh"),
    ]
    issues = check_permissions(entries)
    assert len(issues) >= 2  # sudo + /tmp/
    hosts = {i.entry.host for i in issues}
    assert "host1" in hosts


def test_permission_issue_str():
    entry = make_entry("sudo rm -rf /", host="web01")
    issue = PermissionIssue(entry=entry, reason="uses sudo", severity="critical")
    result = str(issue)
    assert "CRITICAL" in result
    assert "web01" in result
    assert "uses sudo" in result


def test_format_permission_issues_empty():
    result = format_permission_issues([])
    assert "No permission issues" in result


def test_format_permission_issues_lists_issues():
    entry = make_entry("sudo backup.sh", host="db01")
    issue = PermissionIssue(entry=entry, reason="uses sudo", severity="critical")
    result = format_permission_issues([issue])
    assert "db01" in result
    assert "CRITICAL" in result


def test_format_permission_by_severity_groups():
    e1 = make_entry("sudo cmd")
    e2 = make_entry("/tmp/run.sh")
    issues = [
        PermissionIssue(entry=e1, reason="sudo", severity="critical"),
        PermissionIssue(entry=e2, reason="world-writable", severity="warning"),
    ]
    result = format_permission_by_severity(issues)
    assert "CRITICAL" in result
    assert "WARNING" in result


def test_format_permission_summary_counts():
    e = make_entry("sudo cmd")
    issues = [
        PermissionIssue(entry=e, reason="r1", severity="critical"),
        PermissionIssue(entry=e, reason="r2", severity="warning"),
        PermissionIssue(entry=e, reason="r3", severity="critical"),
    ]
    result = format_permission_summary(issues)
    assert "Total issues : 3" in result
    assert "Critical     : 2" in result
    assert "Warning      : 1" in result
