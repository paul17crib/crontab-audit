"""Orchestrates building and filtering notifications using AlertConfig."""

from typing import List
from crontab_audit.reporter import AuditReport
from crontab_audit.notifier import Notification, NotificationBatch, build_notifications
from crontab_audit.alert_config import AlertConfig, DEFAULT_CONFIG


def filter_notifications(
    batch: NotificationBatch,
    config: AlertConfig,
) -> NotificationBatch:
    """Return a new batch containing only notifications that pass config filters."""
    filtered = NotificationBatch()
    for note in batch.notifications:
        if not config.should_include(note.level):
            continue
        filtered.add(note)
        if len(filtered) >= config.max_notifications:
            break
    return filtered


def run_alerts(
    report: AuditReport,
    host: str = "unknown",
    config: AlertConfig = DEFAULT_CONFIG,
) -> NotificationBatch:
    """Build and filter notifications from a report according to config."""
    raw = NotificationBatch()

    if config.notify_on_risk:
        for risk in report.risks:
            from crontab_audit.notifier import Notification
            level = "critical" if config.is_critical_command(risk.entry.command) else "warning"
            raw.add(Notification(
                level=level,
                host=risk.entry.host or host,
                message=f"Risky command: {risk.entry.command}",
                details=risk.reason,
            ))

    if config.notify_on_overlap:
        for overlap in report.overlaps:
            raw.add(Notification(
                level="warning",
                host=overlap.entry_a.host or host,
                message="Schedule overlap detected",
                details=str(overlap),
            ))

    if config.notify_on_parse_errors and report.parse_errors:
        raw.add(Notification(
            level="warning",
            host=host,
            message=f"{len(report.parse_errors)} parse error(s)",
            details="; ".join(report.parse_errors),
        ))

    return filter_notifications(raw, config)


def format_batch(batch: NotificationBatch) -> str:
    """Render a notification batch as a human-readable string."""
    if batch.is_empty():
        return "No notifications."
    lines = [str(n) for n in batch.notifications]
    lines.append(f"\nTotal: {len(batch)} notification(s) "
                 f"({len(batch.criticals())} critical, {len(batch.warnings())} warning)")
    return "\n".join(lines)
