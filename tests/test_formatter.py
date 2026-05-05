"""Tests for crontab_audit.formatter."""

import textwrap
from unittest.mock import MagicMock

from crontab_audit.loader import HostCrontab
from crontab_audit.parser import CrontabEntry
from crontab_audit.formatter import (
    format_host_summary,
    format_all_hosts,
    format_report,
    format_parse_errors,
    SEPARATOR,
)


def make_entry(command: str = "/bin/true", hostname: str = "host1") -> CrontabEntry:
    return CrontabEntry(
        minute="0",
        hour="2",
        day_of_month="*",
        month="*",
        day_of_week="*",
        command=command,
        hostname=hostname,
        raw="0 2 * * * " + command,
    )


def test_format_host_summary_basic():
    hc = HostCrontab(hostname="web01", entries=[make_entry()], parse_errors=[])
    result = format_host_summary(hc)
    assert "web01" in result
    assert "Entries     : 1" in result
    assert "Parse errors: 0" in result


def test_format_host_summary_with_errors():
    hc = HostCrontab(
        hostname="db01",
        entries=[],
        parse_errors=["line 3: too few fields"],
    )
    result = format_host_summary(hc)
    assert "Parse errors: 1" in result
    assert "line 3: too few fields" in result


def test_format_all_hosts_includes_all_hostnames():
    hosts = {
        "alpha": HostCrontab(hostname="alpha", entries=[make_entry(hostname="alpha")]),
        "beta": HostCrontab(hostname="beta", entries=[make_entry(hostname="beta")]),
    }
    result = format_all_hosts(hosts)
    assert "alpha" in result
    assert "beta" in result


def test_format_all_hosts_verbose_includes_entries():
    entry = make_entry(command="/usr/bin/backup.sh", hostname="srv1")
    hosts = {"srv1": HostCrontab(hostname="srv1", entries=[entry])}
    result = format_all_hosts(hosts, verbose=True)
    assert "/usr/bin/backup.sh" in result


def test_format_all_hosts_non_verbose_excludes_entry_details():
    entry = make_entry(command="/usr/bin/secret.sh", hostname="srv1")
    hosts = {"srv1": HostCrontab(hostname="srv1", entries=[entry])}
    result = format_all_hosts(hosts, verbose=False)
    assert "/usr/bin/secret.sh" not in result


def test_format_report_ok_status():
    mock_report = MagicMock()
    mock_report.summary.return_value = "0 risks, 0 overlaps"
    mock_report.detailed.return_value = "detailed info"
    mock_report.has_issues.return_value = False
    result = format_report(mock_report)
    assert "STATUS: OK" in result
    assert SEPARATOR in result


def test_format_report_issues_status():
    mock_report = MagicMock()
    mock_report.summary.return_value = "2 risks, 1 overlap"
    mock_report.detailed.return_value = "detailed info"
    mock_report.has_issues.return_value = True
    result = format_report(mock_report)
    assert "STATUS: ISSUES FOUND" in result


def test_format_report_verbose_uses_detailed():
    mock_report = MagicMock()
    mock_report.detailed.return_value = "very detailed"
    mock_report.has_issues.return_value = False
    result = format_report(mock_report, verbose=True)
    assert "very detailed" in result


def test_format_parse_errors_none():
    hosts = [HostCrontab(hostname="h1", entries=[], parse_errors=[])]
    result = format_parse_errors(hosts)
    assert "No parse errors" in result


def test_format_parse_errors_multiple_hosts():
    hosts = [
        HostCrontab(hostname="h1", parse_errors=["line 1: bad"]),
        HostCrontab(hostname="h2", parse_errors=["line 5: invalid"]),
    ]
    result = format_parse_errors(hosts)
    assert "[h1]" in result
    assert "[h2]" in result
    assert "line 1: bad" in result
    assert "line 5: invalid" in result
