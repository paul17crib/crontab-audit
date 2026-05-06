"""Tests for time_window_report.py."""
from crontab_audit.parser import CrontabEntry
from crontab_audit.time_window import (
    OFFICE_HOURS, OFF_HOURS, WEEKEND, WindowMatch,
)
from crontab_audit.time_window_report import (
    format_window_matches,
    format_window_summary,
    format_off_hours_warnings,
)


def make_entry(command="/bin/job", host="host1", hour="10", dow="1") -> CrontabEntry:
    e = CrontabEntry(
        schedule_fields=["0", hour, "*", "*", dow],
        command=command,
        raw_line=f"0 {hour} * * {dow} {command}",
    )
    e.host = host
    return e


def _match(entry, window):
    return WindowMatch(entry=entry, window=window)


def test_format_window_matches_empty():
    result = format_window_matches([])
    assert "No entries" in result


def test_format_window_matches_groups_by_window():
    e1 = make_entry(command="/bin/a", host="h1")
    e2 = make_entry(command="/bin/b", host="h2")
    matches = [_match(e1, OFFICE_HOURS), _match(e2, OFFICE_HOURS)]
    out = format_window_matches(matches)
    assert "office-hours" in out
    assert "/bin/a" in out
    assert "/bin/b" in out


def test_format_window_matches_multiple_windows():
    e1 = make_entry(command="/bin/day", hour="10", dow="1")
    e2 = make_entry(command="/bin/night", hour="2", dow="1")
    matches = [_match(e1, OFFICE_HOURS), _match(e2, OFF_HOURS)]
    out = format_window_matches(matches)
    assert "office-hours" in out
    assert "off-hours" in out


def test_format_window_summary_empty():
    result = format_window_summary([])
    assert "No window matches" in result


def test_format_window_summary_counts():
    e = make_entry()
    matches = [_match(e, OFFICE_HOURS), _match(e, OFFICE_HOURS), _match(e, WEEKEND)]
    out = format_window_summary(matches)
    assert "office-hours: 2" in out
    assert "weekend: 1" in out


def test_format_off_hours_warnings_empty():
    result = format_off_hours_warnings([])
    assert "No off-hours" in result


def test_format_off_hours_warnings_lists_commands():
    e = make_entry(command="/bin/nightly", host="srv2")
    matches = [_match(e, OFF_HOURS)]
    out = format_off_hours_warnings(matches)
    assert "/bin/nightly" in out
    assert "srv2" in out


def test_format_off_hours_warnings_ignores_other_windows():
    e = make_entry(command="/bin/day")
    matches = [_match(e, OFFICE_HOURS)]
    out = format_off_hours_warnings(matches)
    assert "No off-hours" in out
