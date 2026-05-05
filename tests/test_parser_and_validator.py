"""Tests for crontab parser and validator modules."""

import pytest
from crontab_audit.parser import parse_line, parse_crontab, CrontabParseError, CrontabEntry
from crontab_audit.validator import validate_entry


# --- Parser tests ---

def test_parse_valid_line():
    entry = parse_line("*/5 * * * * /usr/bin/backup.sh", host="web01", line_number=3)
    assert isinstance(entry, CrontabEntry)
    assert entry.minute == "*/5"
    assert entry.command == "/usr/bin/backup.sh"
    assert entry.host == "web01"
    assert entry.line_number == 3


def test_parse_blank_line_returns_none():
    assert parse_line("", host="web01") is None
    assert parse_line("   ", host="web01") is None


def test_parse_comment_line_returns_none():
    assert parse_line("# this is a comment", host="web01") is None


def test_parse_inline_comment():
    entry = parse_line("0 2 * * * /bin/clean.sh # nightly cleanup", host="db01", line_number=7)
    assert entry.comment == "nightly cleanup"
    assert entry.command == "/bin/clean.sh"


def test_parse_too_few_fields_raises():
    with pytest.raises(CrontabParseError):
        parse_line("* * * *", host="web01", line_number=1)


def test_parse_crontab_multi_line():
    content = """# header comment
0 0 * * * /bin/daily.sh
*/15 * * * * /bin/check.sh
"""
    entries = parse_crontab(content, host="app01")
    assert len(entries) == 2
    assert entries[0].command == "/bin/daily.sh"
    assert entries[1].minute == "*/15"


# --- Validator tests ---

def _make_entry(minute="*", hour="*", dom="*", month="*", dow="*", command="/bin/true"):
    return CrontabEntry(
        host="testhost", raw_line="",
        minute=minute, hour=hour,
        day_of_month=dom, month=month,
        day_of_week=dow, command=command,
    )


def test_valid_entry_no_errors():
    entry = _make_entry(minute="*/5", hour="0-23", dom="1", month="6", dow="1,5")
    assert validate_entry(entry) == []


def test_invalid_minute_out_of_range():
    entry = _make_entry(minute="60")
    errors = validate_entry(entry)
    assert any(e.field == "minute" for e in errors)


def test_invalid_hour_out_of_range():
    entry = _make_entry(hour="25")
    errors = validate_entry(entry)
    assert any(e.field == "hour" for e in errors)


def test_invalid_range_reversed():
    entry = _make_entry(hour="22-5")
    errors = validate_entry(entry)
    assert any("Range start > end" in e.message for e in errors)


def test_invalid_step_zero():
    entry = _make_entry(minute="*/0")
    errors = validate_entry(entry)
    assert any(e.field == "minute" for e in errors)


def test_comma_separated_values():
    entry = _make_entry(dow="1,3,5,7")
    errors = validate_entry(entry)
    assert errors == []


def test_comma_with_out_of_range():
    entry = _make_entry(month="1,13")
    errors = validate_entry(entry)
    assert any(e.field == "month" for e in errors)
