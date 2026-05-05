"""Tests for overlap detection."""

import pytest
from crontab_audit.parser import CrontabEntry
from crontab_audit.overlap import find_overlaps, _expand_field, _schedules_overlap


def make_entry(schedule: str, command: str, host: str = "host1") -> CrontabEntry:
    minute, hour, dom, month, dow = schedule.split()
    return CrontabEntry(
        minute=minute, hour=hour, dom=dom, month=month, dow=dow,
        command=command, host=host, raw=f"{schedule} {command}"
    )


def test_expand_star():
    assert _expand_field("*", 0, 5) == {0, 1, 2, 3, 4, 5}


def test_expand_single():
    assert _expand_field("3", 0, 59) == {3}


def test_expand_range():
    assert _expand_field("1-3", 0, 59) == {1, 2, 3}


def test_expand_step():
    assert _expand_field("*/15", 0, 59) == {0, 15, 30, 45}


def test_expand_list():
    assert _expand_field("1,2,3", 0, 59) == {1, 2, 3}


def test_identical_schedules_overlap():
    a = make_entry("0 * * * *", "/usr/bin/foo")
    b = make_entry("0 * * * *", "/usr/bin/bar")
    assert _schedules_overlap(a, b) is True


def test_non_overlapping_schedules():
    a = make_entry("0 6 * * *", "/usr/bin/foo")
    b = make_entry("0 7 * * *", "/usr/bin/bar")
    assert _schedules_overlap(a, b) is False


def test_find_overlaps_same_host():
    a = make_entry("*/5 * * * *", "/usr/bin/foo", host="web1")
    b = make_entry("*/10 * * * *", "/usr/bin/bar", host="web1")
    results = find_overlaps([a, b])
    assert len(results) == 1
    assert results[0].entry_a is a
    assert results[0].entry_b is b


def test_find_overlaps_different_hosts_ignored():
    a = make_entry("0 * * * *", "/usr/bin/foo", host="web1")
    b = make_entry("0 * * * *", "/usr/bin/foo", host="web2")
    results = find_overlaps([a, b])
    assert results == []


def test_overlap_result_str():
    a = make_entry("0 * * * *", "/usr/bin/foo", host="web1")
    b = make_entry("0 * * * *", "/usr/bin/bar", host="web1")
    results = find_overlaps([a, b])
    assert "web1" in str(results[0])
    assert "Overlap" in str(results[0])
