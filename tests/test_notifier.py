"""Tests for the notifier module."""

import pytest
from crontab_audit.parser import CrontabEntry
from crontab_audit.reporter import AuditReport
from crontab_audit.risk import RiskFlag
from crontab_audit.overlap import OverlapResult
from crontab_audit.notifier import Notification, NotificationBatch, build_notifications


def make_entry(command="echo hello", host="host1"):
    return CrontabEntry(
        minute="0", hour="1", dom="*", month="*", dow="*",
        command=command, host=host, raw="0 1 * * * " + command,
    )


def make_report(risks=None, overlaps=None, errors=None):
    return AuditReport(
        entries=[],
        risks=risks or [],
        overlaps=overlaps or [],
        parse_errors=errors or [],
    )


def test_notification_str_no_details():
    n = Notification(level="warning", host="srv1", message="Test msg")
    assert "WARNING" in str(n)
    assert "srv1" in str(n)
    assert "Test msg" in str(n)


def test_notification_str_with_details():
    n = Notification(level="critical", host="srv1", message="Bad", details="extra info")
    result = str(n)
    assert "CRITICAL" in result
    assert "extra info" in result


def test_batch_add_and_len():
    batch = NotificationBatch()
    batch.add(Notification(level="info", host="h", message="m"))
    batch.add(Notification(level="warning", host="h", message="m2"))
    assert len(batch) == 2


def test_batch_criticals_and_warnings():
    batch = NotificationBatch()
    batch.add(Notification(level="critical", host="h", message="c"))
    batch.add(Notification(level="warning", host="h", message="w"))
    batch.add(Notification(level="info", host="h", message="i"))
    assert len(batch.criticals()) == 1
    assert len(batch.warnings()) == 1


def test_batch_is_empty():
    batch = NotificationBatch()
    assert batch.is_empty()
    batch.add(Notification(level="info", host="h", message="m"))
    assert not batch.is_empty()


def test_build_notifications_from_risk():
    entry = make_entry(command="sudo rm -rf /tmp")
    risk = RiskFlag(entry=entry, reason="Uses sudo")
    report = make_report(risks=[risk])
    batch = build_notifications(report, host="host1")
    assert len(batch) >= 1
    assert any("sudo" in n.message.lower() or "sudo" in (n.details or "").lower()
               for n in batch.notifications)


def test_build_notifications_from_overlap():
    a = make_entry()
    b = make_entry(command="echo world")
    overlap = OverlapResult(entry_a=a, entry_b=b)
    report = make_report(overlaps=[overlap])
    batch = build_notifications(report, host="host1")
    assert any("overlap" in n.message.lower() for n in batch.notifications)


def test_build_notifications_parse_errors():
    report = make_report(errors=["bad line 1", "bad line 2"])
    batch = build_notifications(report, host="host1")
    assert any("parse error" in n.message.lower() for n in batch.notifications)


def test_build_notifications_empty_report():
    report = make_report()
    batch = build_notifications(report)
    assert batch.is_empty()
