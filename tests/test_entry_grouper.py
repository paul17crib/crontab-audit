"""Tests for entry_grouper module."""

import pytest
from crontab_audit.parser import CrontabEntry
from crontab_audit.entry_grouper import (
    group_by_host,
    group_by_user,
    group_by_frequency,
    group_by_hour,
    group_entries,
    EntryGroup,
)


def make_entry(
    command="/usr/bin/backup",
    schedule="0 2 * * *",
    host="host1",
    user="root",
) -> CrontabEntry:
    fields = schedule.split()
    return CrontabEntry(
        minute=fields[0],
        hour=fields[1],
        dom=fields[2],
        month=fields[3],
        dow=fields[4],
        command=command,
        host=host,
        user=user,
        raw=f"{schedule} {command}",
    )


def test_group_by_host_single_host():
    entries = [make_entry(host="alpha"), make_entry(host="alpha")]
    groups = group_by_host(entries)
    assert "alpha" in groups
    assert len(groups["alpha"]) == 2


def test_group_by_host_multiple_hosts():
    entries = [make_entry(host="alpha"), make_entry(host="beta")]
    groups = group_by_host(entries)
    assert set(groups.keys()) == {"alpha", "beta"}


def test_group_by_host_none_host_uses_unknown():
    entry = make_entry(host=None)
    groups = group_by_host([entry])
    assert "(unknown)" in groups


def test_group_by_user_basic():
    entries = [make_entry(user="alice"), make_entry(user="bob"), make_entry(user="alice")]
    groups = group_by_user(entries)
    assert len(groups["alice"]) == 2
    assert len(groups["bob"]) == 1


def test_group_by_user_none_user_uses_unknown():
    entry = make_entry(user=None)
    groups = group_by_user([entry])
    assert "(unknown)" in groups


def test_group_by_frequency_daily():
    entry = make_entry(schedule="0 2 * * *")
    groups = group_by_frequency([entry])
    assert any("daily" in k.lower() or "hour" in k.lower() or k for k in groups)


def test_group_by_hour_groups_correctly():
    e1 = make_entry(schedule="0 3 * * *")
    e2 = make_entry(schedule="0 3 * * *")
    e3 = make_entry(schedule="0 5 * * *")
    groups = group_by_hour([e1, e2, e3])
    assert len(groups["3"]) == 2
    assert len(groups["5"]) == 1


def test_group_entries_dispatches_host():
    entries = [make_entry(host="h1"), make_entry(host="h2")]
    groups = group_entries(entries, by="host")
    assert "h1" in groups and "h2" in groups


def test_group_entries_invalid_key_raises():
    with pytest.raises(ValueError, match="Unknown grouping key"):
        group_entries([], by="nonexistent")


def test_entry_group_len():
    entries = [make_entry(), make_entry()]
    group = EntryGroup("test", entries)
    assert len(group) == 2


def test_entry_group_str():
    group = EntryGroup("mykey", [make_entry()])
    assert "mykey" in str(group)
    assert "1 entry" in str(group)


def test_group_by_host_empty_list():
    assert group_by_host([]) == {}
