"""Notification system for crontab audit results."""

from dataclasses import dataclass, field
from typing import List, Optional
from crontab_audit.reporter import AuditReport
from crontab_audit.risk import RiskFlag
from crontab_audit.overlap import OverlapResult


@dataclass
class Notification:
    level: str  # 'info', 'warning', 'critical'
    host: str
    message: str
    details: Optional[str] = None

    def __str__(self) -> str:
        base = f"[{self.level.upper()}] {self.host}: {self.message}"
        if self.details:
            base += f"\n  Details: {self.details}"
        return base


@dataclass
class NotificationBatch:
    notifications: List[Notification] = field(default_factory=list)

    def add(self, notification: Notification) -> None:
        self.notifications.append(notification)

    def criticals(self) -> List[Notification]:
        return [n for n in self.notifications if n.level == "critical"]

    def warnings(self) -> List[Notification]:
        return [n for n in self.notifications if n.level == "warning"]

    def is_empty(self) -> bool:
        return len(self.notifications) == 0

    def __len__(self) -> int:
        return len(self.notifications)


def build_notifications(report: AuditReport, host: str = "unknown") -> NotificationBatch:
    """Convert an AuditReport into a NotificationBatch."""
    batch = NotificationBatch()

    for risk in report.risks:
        level = "critical" if any(
            kw in risk.reason.lower() for kw in ("rm -rf", "sudo", "wget", "curl")
        ) else "warning"
        batch.add(Notification(
            level=level,
            host=risk.entry.host or host,
            message=f"Risky command detected: {risk.entry.command}",
            details=risk.reason,
        ))

    for overlap in report.overlaps:
        batch.add(Notification(
            level="warning",
            host=overlap.entry_a.host or host,
            message="Schedule overlap detected",
            details=str(overlap),
        ))

    if report.parse_errors:
        batch.add(Notification(
            level="warning",
            host=host,
            message=f"{len(report.parse_errors)} parse error(s) found",
            details="; ".join(report.parse_errors),
        ))

    return batch
