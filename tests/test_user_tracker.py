"""Tests for crontab_audit.user_tracker."""

from __future__ import annotations

from crontab_audit.parser import CrontabEntry
from crontab_audit.user_tracker import UserStats, UserReport, build_user_report


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


def test_build_user_report_empty():
    report = build_user_report([])
    assert report.total_users() == 0


def test_build_user_report_single_user():
    entries = [make_entry(user="alice", host="host1")]
    report = build_user_report(entries)
    assert "alice" in report.stats
    assert len(report.stats["alice"].entries) == 1


def test_build_user_report_unknown_user():
    entries = [make_entry(user=None, host="host1")]
    report = build_user_report(entries)
    assert "unknown" in report.stats


def test_build_user_report_multiple_users():
    entries = [
        make_entry(user="alice", host="h1"),
        make_entry(user="bob", host="h1"),
        make_entry(user="alice", host="h2"),
    ]
    report = build_user_report(entries)
    assert report.total_users() == 2
    assert len(report.stats["alice"].entries) == 2
    assert set(report.stats["alice"].hosts) == {"h1", "h2"}


def test_top_users_returns_sorted():
    entries = [
        make_entry(user="alice", host="h1"),
        make_entry(user="alice", host="h1"),
        make_entry(user="bob", host="h1"),
    ]
    report = build_user_report(entries)
    top = report.top_users(2)
    assert top[0].username == "alice"
    assert top[1].username == "bob"


def test_top_users_respects_n():
    entries = [make_entry(user=f"user{i}", host="h") for i in range(10)]
    report = build_user_report(entries)
    assert len(report.top_users(3)) == 3


def test_users_on_host():
    entries = [
        make_entry(user="alice", host="h1"),
        make_entry(user="bob", host="h2"),
        make_entry(user="carol", host="h1"),
    ]
    report = build_user_report(entries)
    users = report.users_on_host("h1")
    assert set(users) == {"alice", "carol"}


def test_user_stats_str():
    stats = UserStats(username="alice", entries=[], hosts=["h1", "h2"])
    s = str(stats)
    assert "alice" in s
    assert "h1" in s
