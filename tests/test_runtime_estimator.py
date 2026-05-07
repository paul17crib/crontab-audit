"""Tests for runtime_estimator and runtime_report modules."""

import pytest
from crontab_audit.parser import CrontabEntry
from crontab_audit.runtime_estimator import (
    estimate_entry_load,
    build_host_load_report,
    top_loaded_entries,
    EntryLoadEstimate,
    HostLoadReport,
)
from crontab_audit.runtime_report import (
    format_host_load,
    format_all_hosts_load,
    format_load_summary,
)


def make_entry(minute="0", hour="*", dom="*", month="*", dow="*",
               command="/usr/bin/backup", host="host1"):
    e = CrontabEntry(
        minute=minute, hour=hour, dom=dom, month=month, dow=dow,
        command=command,
    )
    e.hostname = host
    return e


def test_estimate_entry_load_minutely():
    entry = make_entry(minute="*", hour="*")
    est = estimate_entry_load(entry)
    assert est.frequency_label == "minutely"
    assert est.runs_per_day == pytest.approx(1440.0)
    assert est.total_seconds_per_day == pytest.approx(1440.0 * 2.0)


def test_estimate_entry_load_daily():
    entry = make_entry(minute="0", hour="3")
    est = estimate_entry_load(entry)
    assert est.frequency_label == "daily"
    assert est.runs_per_day == pytest.approx(1.0)
    assert est.total_seconds_per_day == pytest.approx(30.0)


def test_estimate_entry_load_hourly():
    entry = make_entry(minute="0", hour="*")
    est = estimate_entry_load(entry)
    assert est.frequency_label == "hourly"
    assert est.runs_per_day == pytest.approx(24.0)


def test_entry_load_str_contains_command():
    entry = make_entry(command="/bin/myjob")
    est = estimate_entry_load(entry)
    assert "/bin/myjob" in str(est)


def test_build_host_load_report_empty():
    report = build_host_load_report("myhost", [])
    assert report.hostname == "myhost"
    assert report.estimates == []
    assert report.total_seconds_per_day == 0.0
    assert report.total_runs_per_day == 0.0


def test_build_host_load_report_multiple_entries():
    entries = [
        make_entry(minute="0", hour="3", command="/bin/daily"),
        make_entry(minute="*", hour="*", command="/bin/minutely"),
    ]
    report = build_host_load_report("host1", entries)
    assert len(report.estimates) == 2
    assert report.total_runs_per_day > 1.0


def test_host_load_report_str_contains_hostname():
    report = build_host_load_report("webserver", [])
    assert "webserver" in str(report)


def test_top_loaded_entries_returns_n():
    entries = [
        make_entry(minute="0", hour="3", command="/bin/a"),
        make_entry(minute="*", hour="*", command="/bin/b"),
        make_entry(minute="0", hour="*", command="/bin/c"),
    ]
    report = build_host_load_report("h", entries)
    top = top_loaded_entries(report, n=2)
    assert len(top) == 2
    assert top[0].total_seconds_per_day >= top[1].total_seconds_per_day


def test_format_host_load_contains_hostname():
    report = build_host_load_report("srv01", [])
    out = format_host_load(report)
    assert "srv01" in out


def test_format_host_load_with_entries():
    entries = [make_entry(minute="0", hour="6", command="/bin/backup")]
    report = build_host_load_report("srv02", entries)
    out = format_host_load(report)
    assert "/bin/backup" in out
    assert "daily" in out


def test_format_all_hosts_load_empty():
    out = format_all_hosts_load([])
    assert "No host" in out


def test_format_load_summary_counts_hosts():
    r1 = build_host_load_report("a", [make_entry()])
    r2 = build_host_load_report("b", [make_entry(minute="*")])
    out = format_load_summary([r1, r2])
    assert "Hosts   : 2" in out
    assert "Entries : 2" in out


def test_format_load_summary_empty():
    out = format_load_summary([])
    assert "No hosts" in out
