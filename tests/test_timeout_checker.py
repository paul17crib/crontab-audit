"""Tests for timeout_checker and timeout_report."""

import pytest
from crontab_audit.parser import CrontabEntry
from crontab_audit.timeout_checker import (
    TimeoutIssue,
    _is_potentially_long_running,
    check_timeout_risk,
)
from crontab_audit.timeout_report import (
    format_timeout_issues,
    format_timeout_by_severity,
    format_timeout_summary,
)


def make_entry(minute="*", hour="*", dom="*", month="*", dow="*",
               command="echo hi", host="host1", user=None):
    return CrontabEntry(
        minute=minute, hour=hour, dom=dom,
        month=month, dow=dow, command=command,
        host=host, user=user, raw="",
    )


# --- _is_potentially_long_running ---

def test_long_running_rsync():
    assert _is_potentially_long_running("rsync -av /src /dst") is True

def test_long_running_mysqldump():
    assert _is_potentially_long_running("mysqldump mydb > dump.sql") is True

def test_long_running_safe_echo():
    assert _is_potentially_long_running("echo hello") is False

def test_long_running_python_script():
    assert _is_potentially_long_running("/usr/bin/python3 /opt/job.py") is True


# --- check_timeout_risk ---

def test_minutely_rsync_flagged():
    entry = make_entry(minute="*", hour="*", command="rsync -av /a /b")
    issues = check_timeout_risk([entry])
    assert len(issues) == 1
    assert issues[0].severity == "critical"
    assert issues[0].frequency_label == "minutely"

def test_every_5_min_tar_flagged_as_warning():
    entry = make_entry(minute="*/5", hour="*", command="tar czf /tmp/bk.tgz /data")
    issues = check_timeout_risk([entry])
    assert len(issues) == 1
    assert issues[0].severity == "warning"

def test_daily_rsync_not_flagged():
    entry = make_entry(minute="0", hour="2", command="rsync -av /a /b")
    issues = check_timeout_risk([entry])
    assert issues == []

def test_safe_minutely_command_not_flagged():
    entry = make_entry(minute="*", hour="*", command="echo heartbeat")
    issues = check_timeout_risk([entry])
    assert issues == []

def test_multiple_entries_mixed():
    entries = [
        make_entry(minute="*", command="rsync /a /b"),
        make_entry(minute="0", hour="1", command="rsync /a /b"),
        make_entry(minute="*/5", command="wget http://example.com/data.csv"),
    ]
    issues = check_timeout_risk(entries)
    assert len(issues) == 2

def test_issue_str_contains_host_and_command():
    entry = make_entry(minute="*", command="rsync /a /b", host="web01")
    issues = check_timeout_risk([entry])
    assert "web01" in str(issues[0])
    assert "rsync" in str(issues[0])


# --- format helpers ---

def test_format_timeout_issues_empty():
    result = format_timeout_issues([])
    assert "No timeout" in result

def test_format_timeout_issues_includes_entry():
    entry = make_entry(minute="*", command="rsync /a /b", host="h1")
    issues = check_timeout_risk([entry])
    result = format_timeout_issues(issues)
    assert "rsync" in result
    assert "h1" in result

def test_format_timeout_by_severity_groups_correctly():
    entry_crit = make_entry(minute="*", command="rsync /a /b", host="h1")
    entry_warn = make_entry(minute="*/5", command="tar czf /tmp/x /d", host="h2")
    issues = check_timeout_risk([entry_crit, entry_warn])
    result = format_timeout_by_severity(issues)
    assert "CRITICAL" in result
    assert "WARNING" in result

def test_format_timeout_summary_no_issues():
    result = format_timeout_summary([])
    assert "passed" in result

def test_format_timeout_summary_with_issues():
    entry = make_entry(minute="*", command="rsync /a /b")
    issues = check_timeout_risk([entry])
    result = format_timeout_summary(issues)
    assert "critical" in result
