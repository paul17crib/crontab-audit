"""Tests for anomaly_detector module."""
import pytest
from crontab_audit.parser import CrontabEntry
from crontab_audit.anomaly_detector import (
    AnomalyIssue,
    detect_anomalies,
    _is_odd_minute,
    _is_rarely_used_dow,
    _is_suspicious_interval,
)


def make_entry(minute="0", hour="*", dom="*", month="*", dow="*", command="echo hi", host="host1"):
    return CrontabEntry(
        schedule_fields=[minute, hour, dom, month, dow],
        command=command,
        host=host,
        raw_line=f"{minute} {hour} {dom} {month} {dow} {command}",
    )


def test_odd_minute_flags_unusual():
    entry = make_entry(minute="3")
    result = _is_odd_minute(entry)
    assert result is not None
    assert "3" in result


def test_odd_minute_allows_zero():
    entry = make_entry(minute="0")
    assert _is_odd_minute(entry) is None


def test_odd_minute_allows_common_values():
    for m in ("5", "10", "15", "30", "45"):
        entry = make_entry(minute=m)
        assert _is_odd_minute(entry) is None, f"Should allow minute={m}"


def test_odd_minute_ignores_star():
    entry = make_entry(minute="*")
    assert _is_odd_minute(entry) is None


def test_rarely_used_dow_flags_saturday():
    entry = make_entry(dow="6")
    result = _is_rarely_used_dow(entry)
    assert result is not None
    assert "6" in result


def test_rarely_used_dow_flags_sunday():
    entry = make_entry(dow="0")
    result = _is_rarely_used_dow(entry)
    assert result is not None


def test_rarely_used_dow_ignores_star():
    entry = make_entry(dow="*")
    assert _is_rarely_used_dow(entry) is None


def test_rarely_used_dow_ignores_weekday():
    entry = make_entry(dow="1")
    assert _is_rarely_used_dow(entry) is None


def test_suspicious_interval_flags_unusual_step():
    entry = make_entry(minute="*/3")
    result = _is_suspicious_interval(entry)
    assert result is not None
    assert "*/3" in result


def test_suspicious_interval_allows_common_step():
    entry = make_entry(minute="*/5")
    assert _is_suspicious_interval(entry) is None


def test_detect_anomalies_returns_list():
    entries = [make_entry(minute="7"), make_entry(minute="0")]
    issues = detect_anomalies(entries)
    assert isinstance(issues, list)
    assert all(isinstance(i, AnomalyIssue) for i in issues)


def test_detect_anomalies_clean_entry_no_issues():
    entry = make_entry(minute="0", hour="*", dow="*")
    issues = detect_anomalies([entry])
    assert len(issues) == 0


def test_anomaly_issue_str_contains_host_and_reason():
    entry = make_entry(minute="3", host="webserver")
    issue = AnomalyIssue(entry=entry, reason="Unusual minute value: 3", severity="medium")
    s = str(issue)
    assert "webserver" in s
    assert "Unusual minute value: 3" in s
    assert "MEDIUM" in s
