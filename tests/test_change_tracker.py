"""Tests for change_tracker module."""
import pytest
from crontab_audit.parser import CrontabEntry
from crontab_audit.loader import HostCrontab
from crontab_audit.change_tracker import (
    track_changes,
    ChangeReport,
    EntryChange,
    _entry_key,
)


def make_entry(minute="0", hour="2", command="/bin/backup", host="host1"):
    e = CrontabEntry(
        schedule_fields=[minute, hour, "*", "*", "*"],
        command=command,
        raw_line=f"{minute} {hour} * * * {command}",
    )
    e.host = host
    return e


def make_host(hostname, entries):
    return HostCrontab(hostname=hostname, entries=entries, parse_errors=[])


def test_entry_key_combines_schedule_and_command():
    e = make_entry()
    key = _entry_key(e)
    assert "0 2 * * *" in key
    assert "/bin/backup" in key


def test_no_changes_when_identical():
    e = make_entry()
    old = [make_host("h1", [e])]
    new = [make_host("h1", [e])]
    report = track_changes(old, new)
    assert not report.has_changes


def test_detects_added_entry():
    old = [make_host("h1", [])]
    new_entry = make_entry(command="/bin/new")
    new = [make_host("h1", [new_entry])]
    report = track_changes(old, new)
    assert len(report.added) == 1
    assert report.added[0].change_type == "added"
    assert report.added[0].new_entry.command == "/bin/new"


def test_detects_removed_entry():
    old_entry = make_entry(command="/bin/old")
    old = [make_host("h1", [old_entry])]
    new = [make_host("h1", [])]
    report = track_changes(old, new)
    assert len(report.removed) == 1
    assert report.removed[0].change_type == "removed"
    assert report.removed[0].old_entry.command == "/bin/old"


def test_detects_new_host():
    old = []
    new_entry = make_entry(host="h2")
    new = [make_host("h2", [new_entry])]
    report = track_changes(old, new)
    assert len(report.added) == 1
    assert report.added[0].host == "h2"


def test_detects_removed_host():
    old_entry = make_entry(host="h1")
    old = [make_host("h1", [old_entry])]
    new = []
    report = track_changes(old, new)
    assert len(report.removed) == 1
    assert report.removed[0].host == "h1"


def test_has_changes_true_when_added():
    old = [make_host("h1", [])]
    new = [make_host("h1", [make_entry()])]
    report = track_changes(old, new)
    assert report.has_changes


def test_summary_string_format():
    old = [make_host("h1", [])]
    new = [make_host("h1", [make_entry()])]
    report = track_changes(old, new)
    s = report.summary()
    assert "added" in s
    assert "1" in s


def test_entry_change_str():
    e = make_entry(command="/usr/bin/cleanup")
    c = EntryChange(host="h1", change_type="added", new_entry=e)
    assert "ADDED" in str(c)
    assert "/usr/bin/cleanup" in str(c)


def test_multiple_hosts_tracked_independently():
    e1 = make_entry(command="/bin/a", host="h1")
    e2 = make_entry(command="/bin/b", host="h2")
    old = [make_host("h1", [e1]), make_host("h2", [e2])]
    new = [make_host("h1", [e1]), make_host("h2", [])]
    report = track_changes(old, new)
    assert len(report.removed) == 1
    assert report.removed[0].host == "h2"
