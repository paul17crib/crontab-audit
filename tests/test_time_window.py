"""Tests for time_window.py."""
import pytest
from crontab_audit.parser import CrontabEntry
from crontab_audit.time_window import (
    TimeWindow, WindowMatch,
    OFFICE_HOURS, OFF_HOURS, WEEKEND,
    filter_by_window, find_window_matches,
)


def make_entry(minute="0", hour="*", dom="*", month="*", dow="*",
               command="/usr/bin/true", host="host1") -> CrontabEntry:
    e = CrontabEntry(
        schedule_fields=[minute, hour, dom, month, dow],
        command=command,
        raw_line=f"{minute} {hour} {dom} {month} {dow} {command}",
    )
    e.host = host
    return e


def test_office_hours_match_weekday_daytime():
    entry = make_entry(hour="10", dow="2")  # 10:00 on Tuesday
    assert OFFICE_HOURS.matches(entry)


def test_office_hours_no_match_weekend():
    entry = make_entry(hour="10", dow="0")  # 10:00 on Sunday
    assert not OFFICE_HOURS.matches(entry)


def test_office_hours_no_match_night():
    entry = make_entry(hour="2", dow="2")  # 02:00 on Tuesday
    assert not OFFICE_HOURS.matches(entry)


def test_off_hours_match_night():
    entry = make_entry(hour="3", dow="1")
    assert OFF_HOURS.matches(entry)


def test_weekend_match_saturday():
    entry = make_entry(hour="14", dow="6")
    assert WEEKEND.matches(entry)


def test_weekend_no_match_weekday():
    entry = make_entry(hour="14", dow="3")
    assert not WEEKEND.matches(entry)


def test_star_hour_matches_office_hours():
    """An entry with '*' in the hour field runs at all hours, so it matches."""
    entry = make_entry(hour="*", dow="1")
    assert OFFICE_HOURS.matches(entry)


def test_filter_by_window_returns_subset():
    e1 = make_entry(hour="10", dow="2")
    e2 = make_entry(hour="3",  dow="2")
    result = filter_by_window([e1, e2], OFFICE_HOURS)
    assert e1 in result
    assert e2 not in result


def test_find_window_matches_all_windows():
    entry = make_entry(hour="*", dow="*")  # runs always
    matches = find_window_matches([entry])
    window_names = {m.window.name for m in matches}
    assert "office-hours" in window_names
    assert "off-hours" in window_names
    assert "weekend" in window_names


def test_find_window_matches_custom_window():
    custom = TimeWindow(name="midnight", hours=[0], days_of_week=list(range(7)))
    entry = make_entry(hour="0", dow="*")
    matches = find_window_matches([entry], windows=[custom])
    assert len(matches) == 1
    assert matches[0].window.name == "midnight"


def test_window_match_str_contains_host_and_command():
    entry = make_entry(command="/bin/backup", host="srv1")
    m = WindowMatch(entry=entry, window=OFFICE_HOURS)
    s = str(m)
    assert "srv1" in s
    assert "/bin/backup" in s
    assert "office-hours" in s


def test_find_window_matches_empty_entries():
    assert find_window_matches([]) == []
