"""Tests for entry_sorter and entry_sorter_report."""
import pytest
from crontab_audit.parser import CrontabEntry
from crontab_audit.entry_sorter import (
    sort_entries,
    available_sort_keys,
    SortedEntries,
)
from crontab_audit.entry_sorter_report import (
    format_sorted_entries,
    format_sort_summary,
    format_grouped_by_key,
)


def make_entry(
    command="/usr/bin/backup.sh",
    minute="0",
    hour="2",
    dom="*",
    month="*",
    dow="*",
    host="host1",
    user="root",
) -> CrontabEntry:
    return CrontabEntry(
        schedule_fields=[minute, hour, dom, month, dow],
        command=command,
        host=host,
        user=user,
        raw_line=f"{minute} {hour} {dom} {month} {dow} {command}",
    )


def test_available_sort_keys_contains_expected():
    keys = available_sort_keys()
    for k in ("host", "user", "command", "frequency", "schedule"):
        assert k in keys


def test_sort_by_host_ascending():
    entries = [
        make_entry(host="zebra"),
        make_entry(host="alpha"),
        make_entry(host="mango"),
    ]
    result = sort_entries(entries, key="host")
    hosts = [e.host for e in result.entries]
    assert hosts == ["alpha", "mango", "zebra"]


def test_sort_by_host_descending():
    entries = [
        make_entry(host="alpha"),
        make_entry(host="zebra"),
    ]
    result = sort_entries(entries, key="host", reverse=True)
    assert result.entries[0].host == "zebra"


def test_sort_by_command():
    entries = [
        make_entry(command="/z/cmd"),
        make_entry(command="/a/cmd"),
    ]
    result = sort_entries(entries, key="command")
    assert result.entries[0].command == "/a/cmd"


def test_sort_by_frequency_minutely_first():
    minutely = make_entry(minute="*", hour="*")
    daily = make_entry(minute="0", hour="3")
    result = sort_entries([daily, minutely], key="frequency")
    assert result.entries[0] is minutely


def test_sort_invalid_key_raises():
    with pytest.raises(ValueError, match="Unknown sort key"):
        sort_entries([], key="nonexistent")


def test_sorted_entries_str():
    result = SortedEntries(entries=[], sort_key="host", reverse=False)
    assert "host" in str(result)
    assert "asc" in str(result)


def test_format_sorted_entries_includes_host():
    entries = [make_entry(host="myhost", command="/bin/run")]
    result = sort_entries(entries, key="host")
    output = format_sorted_entries(result)
    assert "myhost" in output
    assert "/bin/run" in output


def test_format_sorted_entries_limit():
    entries = [make_entry(host=f"h{i}") for i in range(10)]
    result = sort_entries(entries, key="host")
    output = format_sorted_entries(result, max_rows=3)
    assert "showing 3 of 10" in output


def test_format_sort_summary():
    entries = [make_entry(), make_entry()]
    result = sort_entries(entries, key="command")
    summary = format_sort_summary(result)
    assert "command" in summary
    assert "2" in summary


def test_format_grouped_by_key():
    entries = [
        make_entry(host="alpha"),
        make_entry(host="alpha"),
        make_entry(host="beta"),
    ]
    result = sort_entries(entries, key="host")
    output = format_grouped_by_key(result)
    assert "alpha" in output
    assert "beta" in output
    assert "2 entries" in output
