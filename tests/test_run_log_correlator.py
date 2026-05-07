"""Tests for crontab_audit.run_log_correlator."""

from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional

import pytest

from crontab_audit.parser import CrontabEntry
from crontab_audit.run_log_correlator import (
    RunLogEntry,
    CorrelationIssue,
    correlate_entries,
    _command_key,
    LATE_THRESHOLD_SECONDS,
)


def make_entry(command="/usr/bin/backup.sh", host="host1") -> CrontabEntry:
    return CrontabEntry(
        minute="0", hour="2", dom="*", month="*", dow="*",
        command=command, raw="0 2 * * * " + command, host=host,
    )


def make_log(
    host="host1",
    command="/usr/bin/backup.sh",
    scheduled_offset=0,
    ran_offset: Optional[int] = 0,
    exit_code: Optional[int] = 0,
) -> RunLogEntry:
    base = datetime(2024, 1, 15, 2, 0, 0)
    scheduled_at = base + timedelta(seconds=scheduled_offset)
    ran_at = (base + timedelta(seconds=ran_offset)) if ran_offset is not None else None
    return RunLogEntry(
        host=host,
        command=command,
        scheduled_at=scheduled_at,
        ran_at=ran_at,
        exit_code=exit_code,
    )


# --- RunLogEntry unit tests ---

def test_run_log_is_missed_when_no_ran_at():
    log = make_log(ran_offset=None)
    assert log.is_missed() is True


def test_run_log_not_missed_when_ran_at_set():
    log = make_log(ran_offset=30)
    assert log.is_missed() is False


def test_delay_seconds_positive():
    log = make_log(ran_offset=90)
    assert log.delay_seconds() == pytest.approx(90.0)


def test_delay_seconds_none_when_missed():
    log = make_log(ran_offset=None)
    assert log.delay_seconds() is None


# --- _command_key tests ---

def test_command_key_simple():
    assert _command_key("/usr/bin/backup.sh") == "/usr/bin/backup.sh"


def test_command_key_with_env_prefix():
    assert _command_key("FOO=bar /usr/bin/script.sh") == "/usr/bin/script.sh"


def test_command_key_empty():
    assert _command_key("") == ""


# --- correlate_entries tests ---

def test_no_logs_produces_missed_issue():
    entry = make_entry()
    issues = correlate_entries([entry], [])
    assert len(issues) == 1
    assert issues[0].issue_type == "missed"


def test_clean_run_produces_no_issues():
    entry = make_entry()
    log = make_log(ran_offset=5, exit_code=0)
    issues = correlate_entries([entry], [log])
    assert issues == []


def test_missed_run_flagged():
    entry = make_entry()
    log = make_log(ran_offset=None, exit_code=None)
    issues = correlate_entries([entry], [log])
    assert len(issues) == 1
    assert issues[0].issue_type == "missed"


def test_failed_run_flagged():
    entry = make_entry()
    log = make_log(ran_offset=10, exit_code=1)
    issues = correlate_entries([entry], [log])
    assert len(issues) == 1
    assert issues[0].issue_type == "failed"
    assert "1" in issues[0].detail


def test_late_run_flagged():
    entry = make_entry()
    log = make_log(ran_offset=LATE_THRESHOLD_SECONDS + 60, exit_code=0)
    issues = correlate_entries([entry], [log])
    assert len(issues) == 1
    assert issues[0].issue_type == "late"


def test_on_time_run_not_late():
    entry = make_entry()
    log = make_log(ran_offset=30, exit_code=0)
    issues = correlate_entries([entry], [log], late_threshold=120)
    assert issues == []


def test_correlation_issue_str_contains_type_and_host():
    entry = make_entry(host="web01")
    issue = CorrelationIssue(entry=entry, issue_type="failed", detail="Exit 2.")
    s = str(issue)
    assert "FAILED" in s
    assert "web01" in s


def test_multiple_entries_different_hosts():
    e1 = make_entry(host="host1")
    e2 = make_entry(host="host2")
    log1 = make_log(host="host1", ran_offset=5, exit_code=0)
    # host2 has no log
    issues = correlate_entries([e1, e2], [log1])
    assert len(issues) == 1
    assert issues[0].entry.host == "host2"
