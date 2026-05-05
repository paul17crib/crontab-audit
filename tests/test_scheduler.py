"""Tests for crontab_audit.scheduler module."""

from datetime import datetime
import pytest
from crontab_audit.parser import CrontabEntry
from crontab_audit.scheduler import estimate_next_run, classify_frequency, _field_min


def make_entry(schedule: str, command: str = "echo hi", host: str = "host1") -> CrontabEntry:
    parts = schedule.split() + command.split()
    return CrontabEntry(
        minute=parts[0],
        hour=parts[1],
        day=parts[2],
        month=parts[3],
        weekday=parts[4],
        command=" ".join(parts[5:]),
        host=host,
        raw=schedule + " " + command,
    )


# --- _field_min tests ---

def test_field_min_star():
    assert _field_min("*", 0, 59) == 0


def test_field_min_literal():
    assert _field_min("15", 0, 59) == 15


def test_field_min_list():
    assert _field_min("5,10,20", 0, 59) == 5


def test_field_min_range():
    assert _field_min("10-30", 0, 59) == 10


def test_field_min_step_star():
    assert _field_min("*/5", 0, 59) == 0


def test_field_min_step_base():
    assert _field_min("10/5", 0, 59) == 10


# --- estimate_next_run tests ---

def test_estimate_next_run_returns_datetime():
    entry = make_entry("30 6 * * *")
    result = estimate_next_run(entry, after=datetime(2024, 1, 1, 0, 0))
    assert isinstance(result, datetime)


def test_estimate_next_run_after_anchor():
    entry = make_entry("0 12 * * *")
    anchor = datetime(2024, 6, 15, 8, 0)
    result = estimate_next_run(entry, after=anchor)
    assert result > anchor


def test_estimate_next_run_uses_custom_after():
    entry = make_entry("0 9 * * *")
    anchor = datetime(2024, 3, 10, 10, 0)
    result = estimate_next_run(entry, after=anchor)
    # Should be the next day since 09:00 already passed
    assert result.day == anchor.day + 1 or result.month > anchor.month


# --- classify_frequency tests ---

def test_classify_yearly():
    entry = make_entry("0 0 1 1 *")
    assert classify_frequency(entry) == "yearly"


def test_classify_monthly():
    entry = make_entry("0 0 15 * *")
    assert classify_frequency(entry) == "monthly"


def test_classify_daily():
    entry = make_entry("0 3 * * *")
    assert classify_frequency(entry) == "daily"


def test_classify_hourly():
    entry = make_entry("0 * * * *")
    assert classify_frequency(entry) == "hourly"


def test_classify_sub_hourly_star():
    entry = make_entry("* * * * *")
    assert classify_frequency(entry) == "sub-hourly"


def test_classify_sub_hourly_step():
    entry = make_entry("*/15 * * * *")
    assert classify_frequency(entry) == "sub-hourly"
