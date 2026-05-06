"""Tests for crontab_audit.duplicate_detector."""

import pytest
from crontab_audit.parser import CrontabEntry
from crontab_audit.duplicate_detector import (
    DuplicateGroup,
    _entry_key,
    find_duplicates,
    find_cross_host_duplicates,
    format_duplicate_report,
)


def make_entry(minute="0", hour="*", dom="*", month="*", dow="*",
               command="/usr/bin/backup.sh", host="host1", raw=None):
    return CrontabEntry(
        minute=minute, hour=hour, dom=dom, month=month, dow=dow,
        command=command, host=host, raw=raw or f"{minute} {hour} {dom} {month} {dow} {command}"
    )


def test_entry_key_combines_schedule_and_command():
    entry = make_entry(minute="5", hour="2", command="/bin/clean")
    key = _entry_key(entry)
    assert "5 2 * * *" in key
    assert "/bin/clean" in key


def test_entry_key_same_for_identical_entries():
    e1 = make_entry(host="host1")
    e2 = make_entry(host="host2")
    assert _entry_key(e1) == _entry_key(e2)


def test_entry_key_different_for_different_schedule():
    e1 = make_entry(minute="0")
    e2 = make_entry(minute="5")
    assert _entry_key(e1) != _entry_key(e2)


def test_find_duplicates_detects_same_host_duplicate():
    e1 = make_entry(host="host1")
    e2 = make_entry(host="host1")
    groups = find_duplicates([e1, e2])
    assert len(groups) == 1
    assert len(groups[0].entries) == 2


def test_find_duplicates_no_duplicates_returns_empty():
    e1 = make_entry(command="/bin/a")
    e2 = make_entry(command="/bin/b")
    groups = find_duplicates([e1, e2])
    assert groups == []


def test_find_duplicates_groups_by_schedule_and_command():
    e1 = make_entry(minute="0", command="/bin/a")
    e2 = make_entry(minute="0", command="/bin/a")
    e3 = make_entry(minute="5", command="/bin/b")
    groups = find_duplicates([e1, e2, e3])
    assert len(groups) == 1
    assert groups[0].command == "/bin/a"


def test_duplicate_group_str_includes_hosts():
    e1 = make_entry(host="alpha")
    e2 = make_entry(host="beta")
    group = DuplicateGroup(schedule="0 * * * *", command="/bin/x", entries=[e1, e2])
    text = str(group)
    assert "alpha" in text
    assert "beta" in text
    assert "DUPLICATE" in text


def test_duplicate_group_is_cross_host_true():
    e1 = make_entry(host="host1")
    e2 = make_entry(host="host2")
    group = DuplicateGroup(schedule="0 * * * *", command="/bin/x", entries=[e1, e2])
    assert group.is_cross_host is True


def test_duplicate_group_is_cross_host_false():
    e1 = make_entry(host="host1")
    e2 = make_entry(host="host1")
    group = DuplicateGroup(schedule="0 * * * *", command="/bin/x", entries=[e1, e2])
    assert group.is_cross_host is False


def test_find_cross_host_duplicates_detects_across_hosts():
    host_entries = {
        "alpha": [make_entry(host="alpha", command="/bin/sync")],
        "beta": [make_entry(host="beta", command="/bin/sync")],
    }
    groups = find_cross_host_duplicates(host_entries)
    assert len(groups) == 1
    assert groups[0].is_cross_host


def test_find_cross_host_duplicates_ignores_same_host():
    host_entries = {
        "alpha": [
            make_entry(host="alpha", command="/bin/sync"),
            make_entry(host="alpha", command="/bin/sync"),
        ],
    }
    groups = find_cross_host_duplicates(host_entries)
    assert groups == []


def test_format_duplicate_report_no_duplicates():
    result = format_duplicate_report([])
    assert "No duplicate" in result


def test_format_duplicate_report_with_groups():
    e1 = make_entry(host="h1")
    e2 = make_entry(host="h2")
    group = DuplicateGroup(schedule="0 * * * *", command="/bin/x", entries=[e1, e2])
    result = format_duplicate_report([group])
    assert "1 duplicate group" in result
    assert "h1" in result
    assert "h2" in result
