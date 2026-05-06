"""Tests for crontab_audit.retention and crontab_audit.retention_report."""

from __future__ import annotations

import pytest

from crontab_audit.parser import CrontabEntry
from crontab_audit.retention import (
    RetentionIssue,
    _is_cleanup,
    _is_writer,
    find_retention_issues,
)
from crontab_audit.retention_report import (
    format_retention_by_host,
    format_retention_issues,
    format_retention_summary,
)


def make_entry(command: str, host: str = "host1") -> CrontabEntry:
    return CrontabEntry(
        minute="0",
        hour="1",
        dom="*",
        month="*",
        dow="*",
        command=command,
        raw=f"0 1 * * * {command}",
        host=host,
    )


# --- _is_writer ---

def test_is_writer_redirect():
    assert _is_writer("myapp >> /var/log/app.log")


def test_is_writer_tee():
    assert _is_writer("/usr/bin/myapp | tee /tmp/out.txt")


def test_is_writer_backup():
    assert _is_writer("pg_dump mydb > /backups/db.sql")


def test_is_writer_false_for_safe():
    assert not _is_writer("echo hello")


# --- _is_cleanup ---

def test_is_cleanup_rm():
    assert _is_cleanup("rm -rf /tmp/old_files")


def test_is_cleanup_find_delete():
    assert _is_cleanup("find /var/log -mtime +30 -delete")


def test_is_cleanup_logrotate():
    assert _is_cleanup("logrotate /etc/logrotate.conf")


def test_is_cleanup_false_for_writer():
    assert not _is_cleanup("myapp >> /var/log/app.log")


# --- find_retention_issues ---

def test_no_issues_when_no_writers():
    entries = [make_entry("echo hello"), make_entry("uptime")]
    assert find_retention_issues(entries) == []


def test_issue_flagged_when_writer_no_cleanup():
    entries = [make_entry("pg_dump mydb >> /backups/db.sql")]
    issues = find_retention_issues(entries)
    assert len(issues) == 1
    assert isinstance(issues[0], RetentionIssue)


def test_no_issue_when_writer_and_cleanup_present():
    entries = [
        make_entry("pg_dump mydb >> /backups/db.sql"),
        make_entry("find /backups -mtime +7 -delete"),
    ]
    assert find_retention_issues(entries) == []


def test_issues_isolated_per_host():
    entries = [
        make_entry("pg_dump mydb >> /backups/db.sql", host="host1"),
        make_entry("find /backups -mtime +7 -delete", host="host2"),
    ]
    issues = find_retention_issues(entries)
    # host1 has writer but no cleanup; host2 has cleanup but no writer
    assert len(issues) == 1
    assert issues[0].entry.host == "host1"


def test_retention_issue_str():
    entry = make_entry("myapp >> /var/log/out.log", host="web1")
    issue = RetentionIssue(entry=entry, reason="test reason")
    s = str(issue)
    assert "web1" in s
    assert "test reason" in s


# --- format helpers ---

def test_format_retention_issues_empty():
    assert "No retention" in format_retention_issues([])


def test_format_retention_issues_lists_issues():
    entry = make_entry("pg_dump mydb >> /backups/db.sql")
    issues = find_retention_issues([entry])
    output = format_retention_issues(issues)
    assert "pg_dump" in output


def test_format_retention_by_host_groups():
    entries = [
        make_entry("pg_dump mydb >> /backups/db.sql", host="alpha"),
        make_entry("myapp >> /var/log/app.log", host="beta"),
    ]
    issues = find_retention_issues(entries)
    output = format_retention_by_host(issues)
    assert "alpha" in output
    assert "beta" in output


def test_format_retention_summary_ok():
    assert format_retention_summary([]) == "retention: OK"


def test_format_retention_summary_with_issues():
    entry = make_entry("pg_dump mydb >> /backups/db.sql")
    issues = find_retention_issues([entry])
    summary = format_retention_summary(issues)
    assert "1 issue" in summary
    assert "1 host" in summary
