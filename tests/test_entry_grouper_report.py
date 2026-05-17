"""Tests for entry_grouper_report module."""

from crontab_audit.parser import CrontabEntry
from crontab_audit.entry_grouper import EntryGroup
from crontab_audit.entry_grouper_report import (
    format_group_header,
    format_group,
    format_groups,
    format_group_summary,
    format_largest_groups,
)


def make_entry(command="/bin/run", host="host1", user="root", schedule="0 1 * * *") -> CrontabEntry:
    fields = schedule.split()
    return CrontabEntry(
        minute=fields[0], hour=fields[1], dom=fields[2],
        month=fields[3], dow=fields[4],
        command=command, host=host, user=user,
        raw=f"{schedule} {command}",
    )


def test_format_group_header_singular():
    header = format_group_header("alpha", 1)
    assert "alpha" in header
    assert "1 entry" in header


def test_format_group_header_plural():
    header = format_group_header("beta", 3)
    assert "3 entries" in header


def test_format_group_no_verbose():
    group = EntryGroup("g1", [make_entry()])
    output = format_group(group, verbose=False)
    assert "g1" in output
    assert "/bin/run" not in output


def test_format_group_verbose_shows_command():
    group = EntryGroup("g1", [make_entry(command="/usr/bin/backup")])
    output = format_group(group, verbose=True)
    assert "/usr/bin/backup" in output


def test_format_group_verbose_shows_host():
    group = EntryGroup("g1", [make_entry(host="myhost")])
    output = format_group(group, verbose=True)
    assert "myhost" in output


def test_format_groups_empty():
    result = format_groups({})
    assert "No entries" in result


def test_format_groups_multiple():
    groups = {
        "a": EntryGroup("a", [make_entry()]),
        "b": EntryGroup("b", [make_entry(), make_entry()]),
    }
    output = format_groups(groups)
    assert "a" in output
    assert "b" in output


def test_format_group_summary_counts():
    groups = {
        "x": EntryGroup("x", [make_entry(), make_entry()]),
        "y": EntryGroup("y", [make_entry()]),
    }
    summary = format_group_summary(groups)
    assert "Groups: 2" in summary
    assert "Total entries: 3" in summary


def test_format_group_summary_empty():
    result = format_group_summary({})
    assert "No groups" in result


def test_format_largest_groups_top_n():
    groups = {
        "big": EntryGroup("big", [make_entry(), make_entry(), make_entry()]),
        "small": EntryGroup("small", [make_entry()]),
    }
    output = format_largest_groups(groups, top_n=1)
    assert "big" in output
    assert "small" not in output


def test_format_largest_groups_empty():
    result = format_largest_groups({})
    assert "No groups" in result
