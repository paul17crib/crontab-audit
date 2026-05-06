"""Tests for crontab_audit.overlap_report."""

import pytest
from unittest.mock import MagicMock
from crontab_audit.overlap import OverlapResult
from crontab_audit.overlap_report import (
    format_overlap_pair,
    format_overlap_report,
    format_overlap_summary,
    format_overlaps_by_host,
)


def make_entry(minute="0", hour="*", dom="*", month="*", dow="*", command="/bin/task", hostname="host1"):
    entry = MagicMock()
    entry.schedule_fields = f"{minute} {hour} {dom} {month} {dow}"
    entry.command = command
    entry.hostname = hostname
    return entry


def make_result(entry_a, entry_b, overlap_minutes=None):
    result = MagicMock(spec=OverlapResult)
    result.entry_a = entry_a
    result.entry_b = entry_b
    result.overlap_minutes = overlap_minutes or set()
    return result


def test_format_overlap_pair_same_host():
    a = make_entry(command="/bin/a", hostname="web1")
    b = make_entry(command="/bin/b", hostname="web1")
    result = make_result(a, b)
    output = format_overlap_pair(result)
    assert "[web1]" in output
    assert "/bin/a" in output
    assert "/bin/b" in output


def test_format_overlap_pair_different_hosts():
    a = make_entry(command="/bin/a", hostname="host1")
    b = make_entry(command="/bin/b", hostname="host2")
    result = make_result(a, b)
    output = format_overlap_pair(result)
    assert "[host1]" in output
    assert "[host2]" in output


def test_format_overlap_report_empty():
    output = format_overlap_report([])
    assert "No overlapping" in output


def test_format_overlap_report_with_results():
    a = make_entry(command="/bin/a")
    b = make_entry(command="/bin/b")
    results = [make_result(a, b)]
    output = format_overlap_report(results)
    assert "1 pair" in output
    assert "/bin/a" in output
    assert "/bin/b" in output


def test_format_overlap_report_verbose_shows_minutes():
    a = make_entry(command="/bin/a")
    b = make_entry(command="/bin/b")
    result = make_result(a, b, overlap_minutes={0, 30})
    output = format_overlap_report([result], verbose=True)
    assert "Overlapping minutes" in output


def test_format_overlap_report_verbose_no_minutes_skips_line():
    a = make_entry(command="/bin/a")
    b = make_entry(command="/bin/b")
    result = make_result(a, b, overlap_minutes=set())
    output = format_overlap_report([result], verbose=True)
    assert "Overlapping minutes" not in output


def test_format_overlap_summary_empty():
    output = format_overlap_summary([])
    assert "none" in output


def test_format_overlap_summary_with_results():
    a = make_entry(hostname="host1")
    b = make_entry(hostname="host2")
    results = [make_result(a, b)]
    output = format_overlap_summary(results)
    assert "1 pair" in output
    assert "2 host" in output


def test_format_overlaps_by_host_empty():
    output = format_overlaps_by_host([])
    assert "No overlapping" in output


def test_format_overlaps_by_host_groups_correctly():
    a = make_entry(command="/bin/a", hostname="alpha")
    b = make_entry(command="/bin/b", hostname="alpha")
    results = [make_result(a, b)]
    output = format_overlaps_by_host(results)
    assert "Host: alpha" in output
    assert "/bin/a" in output
    assert "/bin/b" in output


def test_format_overlaps_by_host_multiple_hosts():
    a1 = make_entry(command="/bin/a", hostname="alpha")
    b1 = make_entry(command="/bin/b", hostname="alpha")
    a2 = make_entry(command="/bin/c", hostname="beta")
    b2 = make_entry(command="/bin/d", hostname="beta")
    results = [make_result(a1, b1), make_result(a2, b2)]
    output = format_overlaps_by_host(results)
    assert "Host: alpha" in output
    assert "Host: beta" in output
