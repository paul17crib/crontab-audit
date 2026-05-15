"""Tests for secret_scanner and secret_report modules."""
import pytest
from crontab_audit.parser import CrontabEntry
from crontab_audit.secret_scanner import scan_entry, scan_entries, SecretIssue
from crontab_audit.secret_report import (
    format_secret_issues,
    format_secrets_by_host,
    format_secret_summary,
)


def make_entry(command: str, host: str = "host1") -> CrontabEntry:
    return CrontabEntry(
        minute="0", hour="1", dom="*", month="*", dow="*",
        command=command, host=host, raw=f"0 1 * * * {command}",
    )


def test_scan_entry_detects_password():
    entry = make_entry("mysqldump --password=secret123 db > /tmp/db.sql")
    issues = scan_entry(entry)
    assert any("password" in i.reason.lower() for i in issues)


def test_scan_entry_detects_api_key():
    entry = make_entry("/usr/bin/curl -H 'api_key=ABCDEF123456' https://example.com")
    issues = scan_entry(entry)
    assert any("api key" in i.reason.lower() for i in issues)


def test_scan_entry_detects_token():
    entry = make_entry("/opt/deploy.sh token=ghp_XXXXXXXXXXXXXXXXXXX")
    issues = scan_entry(entry)
    assert any("token" in i.reason.lower() for i in issues)


def test_scan_entry_safe_command_returns_empty():
    entry = make_entry("/usr/bin/find /tmp -mtime +7 -delete")
    issues = scan_entry(entry)
    assert issues == []


def test_scan_entry_detects_aws_secret():
    entry = make_entry("AWS_SECRET_ACCESS_KEY=abc123 /opt/sync.sh")
    issues = scan_entry(entry)
    assert any("aws" in i.reason.lower() for i in issues)


def test_scan_entries_aggregates_multiple():
    entries = [
        make_entry("cmd password=x", host="h1"),
        make_entry("/usr/bin/echo hello", host="h1"),
        make_entry("deploy.sh token=abc", host="h2"),
    ]
    issues = scan_entries(entries)
    assert len(issues) >= 2


def test_secret_issue_str_contains_host():
    entry = make_entry("run.sh password=hunter2", host="webserver")
    issues = scan_entry(entry)
    assert issues
    assert "webserver" in str(issues[0])


def test_secret_issue_str_contains_reason():
    entry = make_entry("run.sh secret=topsecret")
    issues = scan_entry(entry)
    assert issues
    assert "secret" in str(issues[0]).lower()


def test_format_secret_issues_empty():
    result = format_secret_issues([])
    assert "No secret" in result


def test_format_secret_issues_lists_items():
    entry = make_entry("cmd password=abc")
    issues = scan_entry(entry)
    result = format_secret_issues(issues)
    assert "password" in result.lower()


def test_format_secrets_by_host_groups_correctly():
    entries = [
        make_entry("cmd password=x", host="alpha"),
        make_entry("cmd token=y", host="beta"),
    ]
    issues = scan_entries(entries)
    result = format_secrets_by_host(issues)
    assert "alpha" in result
    assert "beta" in result


def test_format_secret_summary_counts():
    entries = [
        make_entry("cmd password=a"),
        make_entry("cmd password=b"),
        make_entry("cmd token=c"),
    ]
    issues = scan_entries(entries)
    result = format_secret_summary(issues)
    assert "issue" in result
    assert "password" in result.lower()


def test_format_secret_summary_no_issues():
    result = format_secret_summary([])
    assert "0 issues" in result
