"""Tests for change_report_formatter module."""
import pytest
from crontab_audit.parser import CrontabEntry
from crontab_audit.loader import HostCrontab
from crontab_audit.change_tracker import track_changes, EntryChange, ChangeReport
from crontab_audit.change_report_formatter import (
    format_change_report,
    format_change_summary,
    format_changes_by_host,
)


def make_entry(minute="0", hour="3", command="/bin/task", host="host1"):
    e = CrontabEntry(
        schedule_fields=[minute, hour, "*", "*", "*"],
        command=command,
        raw_line=f"{minute} {hour} * * * {command}",
    )
    e.host = host
    return e


def make_host(hostname, entries):
    return HostCrontab(hostname=hostname, entries=entries, parse_errors=[])


def test_format_no_changes_message():
    report = ChangeReport(changes=[])
    output = format_change_report(report)
    assert "No changes" in output


def test_format_added_entry_included():
    old = [make_host("h1", [])]
    new = [make_host("h1", [make_entry(command="/bin/new")])]
    report = track_changes(old, new)
    output = format_change_report(report)
    assert "ADDED" in output
    assert "/bin/new" in output


def test_format_removed_entry_included():
    old = [make_host("h1", [make_entry(command="/bin/old")])]
    new = [make_host("h1", [])]
    report = track_changes(old, new)
    output = format_change_report(report)
    assert "REMOVED" in output
    assert "/bin/old" in output


def test_format_summary_counts():
    old = [make_host("h1", [make_entry(command="/bin/gone")])]
    new = [make_host("h1", [make_entry(command="/bin/new")])]
    report = track_changes(old, new)
    output = format_change_report(report)
    assert "added" in output.lower()
    assert "removed" in output.lower()


def test_format_change_summary_standalone():
    old = [make_host("h1", [])]
    new = [make_host("h1", [make_entry()])]
    report = track_changes(old, new)
    s = format_change_summary(report)
    assert "added" in s


def test_format_changes_by_host_no_changes():
    report = ChangeReport(changes=[])
    output = format_changes_by_host(report)
    assert "No changes" in output


def test_format_changes_by_host_groups_by_hostname():
    e1 = make_entry(command="/bin/a", host="alpha")
    e2 = make_entry(command="/bin/b", host="beta")
    old = [make_host("alpha", []), make_host("beta", [])]
    new = [make_host("alpha", [e1]), make_host("beta", [e2])]
    report = track_changes(old, new)
    output = format_changes_by_host(report)
    assert "alpha" in output
    assert "beta" in output
    assert "/bin/a" in output
    assert "/bin/b" in output


def test_format_change_report_includes_header():
    old = [make_host("h1", [])]
    new = [make_host("h1", [make_entry()])]
    report = track_changes(old, new)
    output = format_change_report(report)
    assert "Changes" in output
