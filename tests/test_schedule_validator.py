"""Tests for crontab_audit.schedule_validator."""
import pytest
from crontab_audit.parser import CrontabEntry
from crontab_audit.schedule_validator import (
    ScheduleIssue,
    validate_schedule,
    validate_all,
)


def make_entry(minute="*", hour="*", dom="*", month="*", dow="*", command="echo hi", host="host1"):
    raw = f"{minute} {hour} {dom} {month} {dow} {command}"
    return CrontabEntry(
        minute=minute, hour=hour, dom=dom, month=month, dow=dow,
        command=command, raw=raw, host=host
    )


def test_valid_entry_produces_no_issues():
    entry = make_entry(minute="0", hour="12", dom="1", month="6", dow="1")
    assert validate_schedule(entry) == []


def test_star_fields_produce_no_issues():
    entry = make_entry()
    assert validate_schedule(entry) == []


def test_minute_out_of_range_flagged():
    entry = make_entry(minute="61")
    issues = validate_schedule(entry)
    assert len(issues) == 1
    assert issues[0].field_name == "minute"
    assert "61" in issues[0].reason


def test_hour_out_of_range_flagged():
    entry = make_entry(hour="25")
    issues = validate_schedule(entry)
    assert any(i.field_name == "hour" for i in issues)


def test_dom_zero_flagged():
    entry = make_entry(dom="0")
    issues = validate_schedule(entry)
    assert any(i.field_name == "dom" for i in issues)


def test_month_out_of_range_flagged():
    entry = make_entry(month="13")
    issues = validate_schedule(entry)
    assert any(i.field_name == "month" for i in issues)


def test_dow_value_7_is_valid():
    # 7 is Sunday (alias), should be accepted
    entry = make_entry(dow="7")
    assert validate_schedule(entry) == []


def test_dow_value_8_is_invalid():
    entry = make_entry(dow="8")
    issues = validate_schedule(entry)
    assert any(i.field_name == "dow" for i in issues)


def test_range_inverted_flagged():
    entry = make_entry(minute="50-10")
    issues = validate_schedule(entry)
    assert any("start" in i.reason for i in issues)


def test_range_out_of_bounds_flagged():
    entry = make_entry(hour="0-25")
    issues = validate_schedule(entry)
    assert any(i.field_name == "hour" for i in issues)


def test_step_zero_flagged():
    entry = make_entry(minute="*/0")
    issues = validate_schedule(entry)
    assert any("step" in i.reason for i in issues)


def test_list_with_one_bad_value():
    entry = make_entry(minute="5,65,10")
    issues = validate_schedule(entry)
    assert len(issues) == 1
    assert "65" in issues[0].reason


def test_validate_all_aggregates_multiple_entries():
    entries = [
        make_entry(minute="99"),
        make_entry(hour="30"),
        make_entry(),
    ]
    issues = validate_all(entries)
    assert len(issues) == 2


def test_schedule_issue_str_includes_host_and_field():
    entry = make_entry(minute="99", host="myhost")
    issues = validate_schedule(entry)
    text = str(issues[0])
    assert "myhost" in text
    assert "minute" in text
    assert "WARNING" in text
