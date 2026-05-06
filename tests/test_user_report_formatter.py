"""Tests for crontab_audit.user_report_formatter."""

from __future__ import annotations

from crontab_audit.parser import CrontabEntry
from crontab_audit.user_tracker import build_user_report
from crontab_audit.user_report_formatter import (
    format_user_report,
    format_users_per_host,
    format_user_stats,
)
from crontab_audit.user_tracker import UserStats


def make_entry(command="echo hi", user=None, host=None):
    entry = CrontabEntry(
        minute="0",
        hour="1",
        dom="*",
        month="*",
        dow="*",
        command=command,
        raw="0 1 * * * " + command,
        line_number=1,
    )
    entry.user = user
    entry.host = host
    return entry


def test_format_user_report_empty():
    report = build_user_report([])
    out = format_user_report(report)
    assert "No user data" in out


def test_format_user_report_includes_username():
    entries = [make_entry(user="alice", host="h1")]
    report = build_user_report(entries)
    out = format_user_report(report)
    assert "alice" in out


def test_format_user_report_top_n():
    entries = [
        make_entry(user="alice", host="h1"),
        make_entry(user="alice", host="h1"),
        make_entry(user="bob", host="h1"),
        make_entry(user="carol", host="h1"),
    ]
    report = build_user_report(entries)
    out = format_user_report(report, top_n=2)
    assert "alice" in out
    assert "carol" not in out


def test_format_user_report_total_line():
    entries = [make_entry(user="alice", host="h1"), make_entry(user="bob", host="h2")]
    report = build_user_report(entries)
    out = format_user_report(report)
    assert "Total users: 2" in out


def test_format_users_per_host_empty():
    report = build_user_report([])
    out = format_users_per_host(report)
    assert "No host" in out


def test_format_users_per_host_groups_correctly():
    entries = [
        make_entry(user="alice", host="h1"),
        make_entry(user="bob", host="h1"),
        make_entry(user="carol", host="h2"),
    ]
    report = build_user_report(entries)
    out = format_users_per_host(report)
    assert "h1" in out
    assert "alice" in out
    assert "bob" in out
    assert "h2" in out
    assert "carol" in out


def test_format_user_stats_shows_host():
    stats = UserStats(username="dave", entries=[], hosts=["hostA"])
    out = format_user_stats(stats)
    assert "dave" in out
    assert "hostA" in out
