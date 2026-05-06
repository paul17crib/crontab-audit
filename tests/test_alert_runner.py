"""Tests for alert_runner and alert_config modules."""

import pytest
from crontab_audit.parser import CrontabEntry
from crontab_audit.reporter import AuditReport
from crontab_audit.risk import RiskFlag
from crontab_audit.overlap import OverlapResult
from crontab_audit.alert_config import AlertConfig, from_dict
from crontab_audit.alert_runner import run_alerts, filter_notifications, format_batch
from crontab_audit.notifier import Notification, NotificationBatch


def make_entry(command="echo hi", host="host1"):
    return CrontabEntry(
        minute="*", hour="*", dom="*", month="*", dow="*",
        command=command, host=host, raw="* * * * * " + command,
    )


def make_report(risks=None, overlaps=None, errors=None):
    return AuditReport(
        entries=[],
        risks=risks or [],
        overlaps=overlaps or [],
        parse_errors=errors or [],
    )


def test_alert_config_defaults():
    cfg = AlertConfig()
    assert cfg.notify_on_risk
    assert cfg.notify_on_overlap
    assert cfg.min_level == "warning"


def test_alert_config_should_include():
    cfg = AlertConfig(min_level="warning")
    assert cfg.should_include("warning")
    assert cfg.should_include("critical")
    assert not cfg.should_include("info")


def test_alert_config_is_critical_command():
    cfg = AlertConfig()
    assert cfg.is_critical_command("sudo reboot")
    assert cfg.is_critical_command("wget http://example.com")
    assert not cfg.is_critical_command("echo hello")


def test_from_dict_overrides_fields():
    cfg = from_dict({"notify_on_risk": False, "min_level": "critical", "max_notifications": 5})
    assert not cfg.notify_on_risk
    assert cfg.min_level == "critical"
    assert cfg.max_notifications == 5


def test_from_dict_invalid_level_ignored():
    cfg = from_dict({"min_level": "extreme"})
    assert cfg.min_level == "warning"  # default unchanged


def test_run_alerts_risk_creates_notification():
    entry = make_entry(command="sudo shutdown -h now")
    risk = RiskFlag(entry=entry, reason="Uses sudo")
    report = make_report(risks=[risk])
    batch = run_alerts(report, host="srv1")
    assert len(batch) >= 1


def test_run_alerts_respects_notify_on_risk_false():
    entry = make_entry(command="sudo shutdown -h now")
    risk = RiskFlag(entry=entry, reason="Uses sudo")
    report = make_report(risks=[risk])
    cfg = AlertConfig(notify_on_risk=False)
    batch = run_alerts(report, host="srv1", config=cfg)
    assert all("risk" not in n.message.lower() and "risky" not in n.message.lower()
               for n in batch.notifications)


def test_run_alerts_max_notifications_respected():
    entries = [make_entry(command=f"sudo cmd{i}") for i in range(20)]
    risks = [RiskFlag(entry=e, reason="sudo") for e in entries]
    report = make_report(risks=risks)
    cfg = AlertConfig(max_notifications=3)
    batch = run_alerts(report, config=cfg)
    assert len(batch) <= 3


def test_format_batch_empty():
    batch = NotificationBatch()
    result = format_batch(batch)
    assert "No notifications" in result


def test_format_batch_with_entries():
    batch = NotificationBatch()
    batch.add(Notification(level="critical", host="h", message="bad thing"))
    batch.add(Notification(level="warning", host="h", message="watch out"))
    result = format_batch(batch)
    assert "bad thing" in result
    assert "watch out" in result
    assert "Total: 2" in result
