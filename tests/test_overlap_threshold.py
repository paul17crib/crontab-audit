"""Tests for overlap_threshold module."""

import pytest
from crontab_audit.parser import CrontabEntry
from crontab_audit.overlap import OverlapResult
from crontab_audit.overlap_threshold import ThresholdViolation, check_overlap_thresholds


def make_entry(minute="0", hour="*", dom="*", month="*", dow="*", command="/bin/task", host="host1"):
    return CrontabEntry(
        minute=minute, hour=hour, dom=dom, month=month, dow=dow,
        command=command, host=host, raw=f"{minute} {hour} {dom} {month} {dow} {command}"
    )


def make_result(a, b):
    return OverlapResult(entry_a=a, entry_b=b)


def test_no_violations_below_threshold():
    a = make_entry(command="/bin/a")
    b = make_entry(command="/bin/b")
    overlaps = [make_result(a, b)]
    violations = check_overlap_thresholds(overlaps, threshold=3)
    assert violations == []


def test_violation_at_threshold():
    a = make_entry(command="/bin/a")
    b = make_entry(command="/bin/b")
    c = make_entry(command="/bin/c")
    # 'a' overlaps with both b and c -> count=2, threshold=2 -> violation
    overlaps = [make_result(a, b), make_result(a, c)]
    violations = check_overlap_thresholds(overlaps, threshold=2)
    commands = [v.entry.command for v in violations]
    assert "/bin/a" in commands


def test_violation_count_is_correct():
    a = make_entry(command="/bin/a")
    b = make_entry(command="/bin/b")
    c = make_entry(command="/bin/c")
    d = make_entry(command="/bin/d")
    overlaps = [make_result(a, b), make_result(a, c), make_result(a, d)]
    violations = check_overlap_thresholds(overlaps, threshold=3)
    assert len(violations) == 1
    assert violations[0].overlap_count == 3


def test_violation_partners_populated():
    a = make_entry(command="/bin/a")
    b = make_entry(command="/bin/b")
    c = make_entry(command="/bin/c")
    overlaps = [make_result(a, b), make_result(a, c)]
    violations = check_overlap_thresholds(overlaps, threshold=2)
    v = next(v for v in violations if v.entry.command == "/bin/a")
    partner_commands = {e.command for e in v.overlapping_with}
    assert partner_commands == {"/bin/b", "/bin/c"}


def test_empty_overlaps_returns_empty():
    violations = check_overlap_thresholds([], threshold=1)
    assert violations == []


def test_invalid_threshold_raises():
    with pytest.raises(ValueError, match="threshold must be >= 1"):
        check_overlap_thresholds([], threshold=0)


def test_violation_str_contains_host_and_command():
    a = make_entry(command="/bin/a", host="webserver")
    b = make_entry(command="/bin/b")
    c = make_entry(command="/bin/c")
    overlaps = [make_result(a, b), make_result(a, c)]
    violations = check_overlap_thresholds(overlaps, threshold=2)
    s = str(violations[0])
    assert "webserver" in s
    assert "/bin/a" in s
    assert "limit=2" in s


def test_sorted_by_overlap_count_descending():
    a = make_entry(command="/bin/a")
    b = make_entry(command="/bin/b")
    c = make_entry(command="/bin/c")
    d = make_entry(command="/bin/d")
    # a overlaps 3 times, b overlaps 2 times
    overlaps = [
        make_result(a, c), make_result(a, d), make_result(a, b),
        make_result(b, c), make_result(b, d),
    ]
    violations = check_overlap_thresholds(overlaps, threshold=2)
    counts = [v.overlap_count for v in violations]
    assert counts == sorted(counts, reverse=True)


def test_each_entry_counted_once():
    a = make_entry(command="/bin/a")
    b = make_entry(command="/bin/b")
    overlaps = [make_result(a, b)]
    violations = check_overlap_thresholds(overlaps, threshold=1)
    commands = [v.entry.command for v in violations]
    # Both a and b appear once each
    assert len(commands) == 2
    assert "/bin/a" in commands
    assert "/bin/b" in commands
