"""Tests for crontab_audit.entry_deduplicator."""

import pytest
from crontab_audit.parser import CrontabEntry
from crontab_audit.entry_deduplicator import (
    DeduplicationResult,
    _entry_key,
    deduplicate_entries,
)


def make_entry(
    minute="0",
    hour="2",
    dom="*",
    month="*",
    dow="*",
    command="/usr/bin/backup.sh",
    host="host1",
    user=None,
) -> CrontabEntry:
    entry = CrontabEntry(
        schedule_fields=[minute, hour, dom, month, dow],
        command=command,
    )
    entry.host = host
    entry.user = user
    return entry


def test_entry_key_includes_host_by_default():
    e = make_entry(host="hostA")
    key = _entry_key(e, cross_host=False)
    assert "hostA" in key


def test_entry_key_excludes_host_when_cross_host():
    e = make_entry(host="hostA")
    key = _entry_key(e, cross_host=True)
    assert "hostA" not in key


def test_entry_key_includes_schedule_and_command():
    e = make_entry(minute="5", hour="3", command="/bin/foo")
    key = _entry_key(e)
    assert "5" in key
    assert "3" in key
    assert "/bin/foo" in key


def test_deduplicate_empty_list():
    result = deduplicate_entries([])
    assert result.unique == []
    assert result.duplicates == []


def test_deduplicate_no_duplicates():
    e1 = make_entry(command="/bin/a", host="h1")
    e2 = make_entry(command="/bin/b", host="h1")
    result = deduplicate_entries([e1, e2])
    assert result.unique_count == 2
    assert result.duplicate_count == 0


def test_deduplicate_same_host_duplicate_detected():
    e1 = make_entry(command="/bin/backup", host="h1")
    e2 = make_entry(command="/bin/backup", host="h1")
    result = deduplicate_entries([e1, e2])
    assert result.unique_count == 1
    assert result.duplicate_count == 1


def test_deduplicate_keep_first_retains_first_occurrence():
    e1 = make_entry(command="/bin/backup", host="h1", user="root")
    e2 = make_entry(command="/bin/backup", host="h1", user="admin")
    result = deduplicate_entries([e1, e2], keep="first")
    assert result.unique[0].user == "root"


def test_deduplicate_keep_last_retains_last_occurrence():
    e1 = make_entry(command="/bin/backup", host="h1", user="root")
    e2 = make_entry(command="/bin/backup", host="h1", user="admin")
    result = deduplicate_entries([e1, e2], keep="last")
    assert result.unique[0].user == "admin"


def test_deduplicate_cross_host_detects_same_job_on_different_hosts():
    e1 = make_entry(command="/bin/sync", host="h1")
    e2 = make_entry(command="/bin/sync", host="h2")
    result = deduplicate_entries([e1, e2], cross_host=True)
    assert result.unique_count == 1
    assert result.duplicate_count == 1


def test_deduplicate_cross_host_false_keeps_both_hosts():
    e1 = make_entry(command="/bin/sync", host="h1")
    e2 = make_entry(command="/bin/sync", host="h2")
    result = deduplicate_entries([e1, e2], cross_host=False)
    assert result.unique_count == 2
    assert result.duplicate_count == 0


def test_deduplication_result_str():
    result = DeduplicationResult(unique=[make_entry()], duplicates=[make_entry()])
    s = str(result)
    assert "1 unique" in s
    assert "1 duplicates" in s


def test_invalid_keep_raises_value_error():
    with pytest.raises(ValueError, match="keep must be"):
        deduplicate_entries([make_entry()], keep="middle")
