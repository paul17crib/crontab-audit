"""Configuration for alert thresholds and notification channels."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class AlertConfig:
    """Controls which issues trigger notifications and at what severity."""
    notify_on_risk: bool = True
    notify_on_overlap: bool = True
    notify_on_parse_errors: bool = True
    critical_commands: List[str] = field(default_factory=lambda: [
        "rm -rf", "sudo", "wget", "curl", "chmod 777", "dd if="
    ])
    min_level: str = "warning"  # 'info', 'warning', 'critical'
    max_notifications: int = 100

    def should_include(self, level: str) -> bool:
        order = {"info": 0, "warning": 1, "critical": 2}
        return order.get(level, 0) >= order.get(self.min_level, 1)

    def is_critical_command(self, command: str) -> bool:
        cmd_lower = command.lower()
        return any(kw in cmd_lower for kw in self.critical_commands)


DEFAULT_CONFIG = AlertConfig()


def from_dict(data: dict) -> AlertConfig:
    """Build an AlertConfig from a plain dictionary (e.g. loaded from JSON/YAML)."""
    cfg = AlertConfig()
    if "notify_on_risk" in data:
        cfg.notify_on_risk = bool(data["notify_on_risk"])
    if "notify_on_overlap" in data:
        cfg.notify_on_overlap = bool(data["notify_on_overlap"])
    if "notify_on_parse_errors" in data:
        cfg.notify_on_parse_errors = bool(data["notify_on_parse_errors"])
    if "critical_commands" in data:
        cfg.critical_commands = list(data["critical_commands"])
    if "min_level" in data:
        if data["min_level"] in ("info", "warning", "critical"):
            cfg.min_level = data["min_level"]
    if "max_notifications" in data:
        cfg.max_notifications = int(data["max_notifications"])
    return cfg
