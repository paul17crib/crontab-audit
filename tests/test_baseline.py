"""Tests for crontab_audit.baseline module."""

import json
import pytest
from unittest.mock import patch, MagicMock

from crontab_audit.parser import CrontabEntry
from crontab_audit.loader import HostCrontab
from crontab_audit.baseline import (
    BaselineReport,
    compare_against_baseline,
    save_baseline,
)


def make_entry(minute="0", hour="*", dom="*", month="*", dow="*", command="/bin/task", hostname="host1"):
    e = CrontabEntry(
        minute=minute, hour=hour, dom=dom, month=month, dow=dow, command=command
    )
    e.hostname = hostname
    return e


def make_host(hostname="host1", entries=None):
    return HostCrontab(hostname=hostname, entries=entries or [], parse_errors=[])


def test_baseline_report_no_changes():
    report = BaselineReport()
    assert not report.has_changes
    assert "No changes" in report.summary()


def test_baseline_report_new_host():
    report = BaselineReport(new_hosts=["newhost"])
    assert report.has_changes
    assert "newhost" in report.summary()


def test_baseline_report_removed_host():
    report = BaselineReport(removed_hosts=["oldhost"])
    assert report.has_changes
    assert "oldhost" in report.summary()


def test_compare_returns_none_when_no_snapshot():
    with patch("crontab_audit.baseline.load_snapshot", return_value=None):
        result = compare_against_baseline([make_host()], "/fake/path.json")
    assert result is None


def test_compare_detects_new_host():
    current = [make_host("host1"), make_host("host2")]
    baseline_data = [
        {"hostname": "host1", "entries": []}
    ]
    with patch("crontab_audit.baseline.load_snapshot", return_value=baseline_data):
        report = compare_against_baseline(current, "/fake/path.json")
    assert report is not None
    assert "host2" in report.new_hosts
    assert report.has_changes


def test_compare_detects_removed_host():
    current = [make_host("host1")]
    baseline_data = [
        {"hostname": "host1", "entries": []},
        {"hostname": "host2", "entries": []},
    ]
    with patch("crontab_audit.baseline.load_snapshot", return_value=baseline_data):
        report = compare_against_baseline(current, "/fake/path.json")
    assert report is not None
    assert "host2" in report.removed_hosts


def test_compare_no_changes_same_entries():
    entry_dict = {
        "minute": "0", "hour": "1", "dom": "*",
        "month": "*", "dow": "*", "command": "/bin/backup",
        "hostname": "host1",
    }
    current_entry = make_entry(minute="0", hour="1", command="/bin/backup", hostname="host1")
    current = [make_host("host1", entries=[current_entry])]
    baseline_data = [{"hostname": "host1", "entries": [entry_dict]}]

    with patch("crontab_audit.baseline.load_snapshot", return_value=baseline_data):
        report = compare_against_baseline(current, "/fake/path.json")

    assert report is not None
    assert not report.new_hosts
    assert not report.removed_hosts
    assert not report.has_changes


def test_save_baseline_writes_json(tmp_path):
    """Test that save_baseline serializes host crontabs to JSON correctly."""
    output_file = tmp_path / "baseline.json"
    entry = make_entry(minute="30", hour="2", command="/bin/cleanup", hostname="host1")
    hosts = [make_host("host1", entries=[entry])]

    save_baseline(hosts, str(output_file))

    assert output_file.exists()
    data = json.loads(output_file.read_text())
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["hostname"] == "host1"
