"""Tests for crontab_audit.conflict_detector."""

import pytest
from crontab_audit.parser import CrontabEntry
from crontab_audit.conflict_detector import (
    ConflictIssue,
    _command_key,
    _minute_set,
    _hour_set,
    find_conflicts,
)


def make_entry(schedule: str, command: str, host: str = "host1") -> CrontabEntry:
    e = CrontabEntry(schedule_fields=schedule, command=command)
    e.host = host
    return e


# --- _command_key ---

def test_command_key_simple():
    e = make_entry("* * * * *", "/usr/bin/backup.sh")
    assert _command_key(e) == "/usr/bin/backup.sh"


def test_command_key_strips_env_prefix():
    e = make_entry("* * * * *", "FOO=bar /usr/bin/backup.sh")
    assert _command_key(e) == "/usr/bin/backup.sh"


def test_command_key_bare_word():
    e = make_entry("* * * * *", "backup")
    assert _command_key(e) == "backup"


# --- _minute_set / _hour_set ---

def test_minute_set_star():
    e = make_entry("* * * * *", "cmd")
    assert len(_minute_set(e)) == 60


def test_minute_set_literal():
    e = make_entry("30 * * * *", "cmd")
    assert _minute_set(e) == {30}


def test_hour_set_range():
    e = make_entry("0 9-11 * * *", "cmd")
    assert _hour_set(e) == {9, 10, 11}


# --- find_conflicts ---

def test_find_conflicts_no_entries():
    assert find_conflicts([]) == []


def test_find_conflicts_single_entry_no_issue():
    entries = [make_entry("0 * * * *", "/bin/run")]
    assert find_conflicts(entries) == []


def test_find_conflicts_different_commands_no_issue():
    entries = [
        make_entry("0 9 * * *", "/bin/alpha"),
        make_entry("0 9 * * *", "/bin/beta"),
    ]
    assert find_conflicts(entries) == []


def test_find_conflicts_exact_duplicate_no_conflict():
    # exact duplicates are handled by duplicate_detector, not here
    entries = [
        make_entry("0 9 * * *", "/bin/run"),
        make_entry("0 9 * * *", "/bin/run"),
    ]
    assert find_conflicts(entries) == []


def test_find_conflicts_overlapping_schedules_same_command():
    entries = [
        make_entry("0 * * * *", "/bin/run"),
        make_entry("0 9-17 * * *", "/bin/run"),
    ]
    results = find_conflicts(entries)
    assert len(results) == 1
    assert isinstance(results[0], ConflictIssue)
    assert results[0].host == "host1"
    assert "overlapping" in results[0].reason


def test_find_conflicts_non_overlapping_hours_no_issue():
    entries = [
        make_entry("0 8 * * *", "/bin/run"),
        make_entry("0 20 * * *", "/bin/run"),
    ]
    assert find_conflicts(entries) == []


def test_find_conflicts_cross_host_not_flagged():
    entries = [
        make_entry("0 * * * *", "/bin/run", host="host1"),
        make_entry("0 9 * * *", "/bin/run", host="host2"),
    ]
    assert find_conflicts(entries) == []


def test_conflict_issue_str():
    a = make_entry("0 * * * *", "/bin/run")
    b = make_entry("0 9 * * *", "/bin/run")
    issue = ConflictIssue(host="host1", entry_a=a, entry_b=b, reason="overlapping minute+hour windows for same command")
    text = str(issue)
    assert "CONFLICT" in text
    assert "/bin/run" in text
    assert "host1" in text
