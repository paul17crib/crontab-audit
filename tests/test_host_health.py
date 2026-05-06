"""Tests for host_health scoring and host_health_report formatting."""

import pytest
from crontab_audit.parser import CrontabEntry
from crontab_audit.loader import HostCrontab
from crontab_audit.host_health import (
    score_host,
    score_all_hosts,
    HostHealthScore,
    _grade,
)
from crontab_audit.host_health_report import (
    format_health_report,
    format_worst_hosts,
    format_score_row,
)


def make_entry(minute="0", hour="1", dom="*", month="*", dow="*",
               command="/usr/bin/backup.sh", host="host1", user=None):
    e = CrontabEntry(
        minute=minute, hour=hour, dom=dom, month=month, dow=dow,
        command=command, raw=f"{minute} {hour} {dom} {month} {dow} {command}",
        source_host=host, user=user,
    )
    return e


def make_host(hostname="host1", entries=None, parse_errors=None):
    return HostCrontab(
        hostname=hostname,
        entries=entries or [],
        parse_errors=parse_errors or [],
    )


# --- _grade ---

def test_grade_a():
    assert _grade(100) == "A"
    assert _grade(90) == "A"


def test_grade_b():
    assert _grade(80) == "B"
    assert _grade(75) == "B"


def test_grade_c():
    assert _grade(60) == "C"


def test_grade_d():
    assert _grade(40) == "D"


def test_grade_f():
    assert _grade(10) == "F"
    assert _grade(0) == "F"


# --- score_host ---

def test_score_host_perfect_clean_host():
    host = make_host(entries=[make_entry()])
    result = score_host(host)
    assert result.score == 100
    assert result.risk_count == 0
    assert result.overlap_count == 0
    assert result.penalties == []


def test_score_host_risky_command_reduces_score():
    entry = make_entry(command="rm -rf /tmp/data")
    host = make_host(entries=[entry])
    result = score_host(host)
    assert result.risk_count >= 1
    assert result.score < 100


def test_score_host_parse_errors_reduce_score():
    host = make_host(entries=[], parse_errors=["bad line 1", "bad line 2"])
    result = score_host(host)
    assert result.parse_error_count == 2
    assert result.score <= 100 - 12  # 2 * 6


def test_score_host_score_never_below_zero():
    risky_entries = [
        make_entry(command="rm -rf /") for _ in range(20)
    ]
    host = make_host(entries=risky_entries, parse_errors=["e"] * 10)
    result = score_host(host)
    assert result.score >= 0


def test_score_host_str_contains_hostname():
    host = make_host(hostname="webserver", entries=[make_entry()])
    result = score_host(host)
    assert "webserver" in str(result)


# --- score_all_hosts ---

def test_score_all_hosts_sorted_best_first():
    clean = make_host(hostname="clean", entries=[make_entry()])
    risky = make_host(
        hostname="risky",
        entries=[make_entry(command="rm -rf /var") for _ in range(3)],
    )
    results = score_all_hosts([risky, clean])
    assert results[0].hostname == "clean"
    assert results[1].hostname == "risky"


def test_score_all_hosts_empty():
    assert score_all_hosts([]) == []


# --- report formatting ---

def test_format_health_report_no_hosts():
    assert format_health_report([]) == "No hosts to report."


def test_format_health_report_includes_hostname():
    host = make_host(hostname="alpha", entries=[make_entry()])
    score = score_host(host)
    report = format_health_report([score])
    assert "alpha" in report
    assert "Host Health Report" in report


def test_format_health_report_verbose_shows_penalties():
    host = make_host(
        hostname="beta",
        entries=[make_entry(command="wget http://example.com/payload")],
    )
    score = score_host(host)
    report = format_health_report([score], verbose=True)
    if score.penalties:
        assert any(p in report for p in score.penalties)


def test_format_worst_hosts_empty():
    assert "No hosts" in format_worst_hosts([])


def test_format_worst_hosts_returns_n_entries():
    hosts = [
        make_host(hostname=f"host{i}", entries=[make_entry()])
        for i in range(6)
    ]
    scores = score_all_hosts(hosts)
    report = format_worst_hosts(scores, n=3)
    assert "Bottom 3" in report


def test_format_score_row_contains_bar():
    host = make_host(entries=[make_entry()])
    hs = score_host(host)
    row = format_score_row(hs)
    assert "#" in row or "-" in row
    assert "/100" in row
