"""Tests for crontab_audit.resource_monitor."""
import pytest
from crontab_audit.parser import CrontabEntry
from crontab_audit.resource_monitor import (
    check_resource_risk,
    _is_heavy_command,
    _is_high_io,
    _runs_frequently,
    ResourceIssue,
)


def make_entry(minute="0", hour="3", dom="*", month="*", dow="*",
               command="echo ok", host="host1"):
    return CrontabEntry(
        minute=minute, hour=hour, dom=dom, month=month, dow=dow,
        command=command, host=host,
    )


def test_is_heavy_command_rsync():
    assert _is_heavy_command("rsync -av /src /dst") is True


def test_is_heavy_command_mysqldump():
    assert _is_heavy_command("mysqldump -u root mydb > dump.sql") is True


def test_is_heavy_command_safe_echo():
    assert _is_heavy_command("echo hello") is False


def test_is_high_io_tee():
    assert _is_high_io("/usr/bin/logger | tee /var/log/out.log") is True


def test_is_high_io_redirect():
    assert _is_high_io("ls >> /tmp/listing.txt") is True


def test_is_high_io_safe_command():
    assert _is_high_io("echo hello") is False


def test_runs_frequently_star_star():
    entry = make_entry(minute="*", hour="*")
    assert _runs_frequently(entry) is True


def test_runs_frequently_step_small():
    entry = make_entry(minute="*/5", hour="*")
    assert _runs_frequently(entry) is True


def test_runs_frequently_step_large():
    entry = make_entry(minute="*/30", hour="*")
    assert _runs_frequently(entry) is False


def test_runs_frequently_fixed_hour():
    entry = make_entry(minute="0", hour="3")
    assert _runs_frequently(entry) is False


def test_check_resource_risk_heavy_and_frequent_is_high():
    entry = make_entry(minute="*", hour="*", command="rsync -av /a /b")
    issues = check_resource_risk([entry])
    assert len(issues) == 1
    assert issues[0].severity == "high"


def test_check_resource_risk_heavy_and_io_is_medium():
    entry = make_entry(minute="0", hour="2", command="tar -czf backup.tar.gz /data >> /log/backup.log")
    issues = check_resource_risk([entry])
    assert any(i.severity == "medium" for i in issues)


def test_check_resource_risk_heavy_only_is_low():
    entry = make_entry(minute="0", hour="4", command="python /opt/scripts/report.py")
    issues = check_resource_risk([entry])
    assert len(issues) == 1
    assert issues[0].severity == "low"


def test_check_resource_risk_safe_entry_no_issues():
    entry = make_entry(minute="0", hour="6", command="echo heartbeat")
    issues = check_resource_risk([entry])
    assert issues == []


def test_resource_issue_str_contains_host_and_command():
    entry = make_entry(minute="*", hour="*", command="rsync -av /a /b", host="srv1")
    issue = ResourceIssue(entry=entry, reason="test reason", severity="high")
    text = str(issue)
    assert "srv1" in text
    assert "rsync" in text
    assert "HIGH" in text


def test_check_resource_risk_multiple_entries():
    entries = [
        make_entry(minute="*", hour="*", command="rsync /a /b"),
        make_entry(minute="0", hour="1", command="echo ok"),
        make_entry(minute="*/10", hour="*", command="pg_dump mydb >> /tmp/dump"),
    ]
    issues = check_resource_risk(entries)
    assert len(issues) >= 2
