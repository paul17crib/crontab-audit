"""Flag risky crontab entries based on heuristics."""

from dataclasses import dataclass
from typing import List
from .parser import CrontabEntry

RISKY_PATTERNS = [
    ("rm -rf", "destructive remove command"),
    ("wget", "remote file download"),
    ("curl", "remote request or download"),
    ("chmod 777", "overly permissive file mode"),
    ("> /dev/sda", "direct disk write"),
    ("dd if=", "raw disk operation"),
    ("/etc/passwd", "access to sensitive file"),
    ("/etc/shadow", "access to sensitive file"),
    ("sudo", "privilege escalation"),
    ("bash -i", "interactive shell invocation"),
]


@dataclass
class RiskFlag:
    entry: CrontabEntry
    pattern: str
    reason: str

    def __str__(self) -> str:
        return (
            f"[RISK] Host '{self.entry.host}' command '{self.entry.command}' "
            f"matches pattern '{self.pattern}': {self.reason}"
        )


def flag_risky_entries(entries: List[CrontabEntry]) -> List[RiskFlag]:
    """Return a list of RiskFlag objects for entries matching risky patterns."""
    flags: List[RiskFlag] = []
    for entry in entries:
        cmd_lower = entry.command.lower()
        for pattern, reason in RISKY_PATTERNS:
            if pattern.lower() in cmd_lower:
                flags.append(RiskFlag(entry=entry, pattern=pattern, reason=reason))
                break  # one flag per entry is enough
    return flags


def is_high_frequency(entry: CrontabEntry) -> bool:
    """Return True if the entry runs more often than every 5 minutes."""
    minute_field = entry.schedule_fields()[0]
    if minute_field == "*":
        return True
    if minute_field.startswith("*/"):
        try:
            step = int(minute_field[2:])
            return step < 5
        except ValueError:
            return False
    return False


def flag_high_frequency(entries: List[CrontabEntry]) -> List[RiskFlag]:
    """Return RiskFlag entries for schedules running more than once every 5 min."""
    flags: List[RiskFlag] = []
    for entry in entries:
        if is_high_frequency(entry):
            flags.append(
                RiskFlag(
                    entry=entry,
                    pattern=entry.schedule_fields()[0],
                    reason="runs more frequently than every 5 minutes",
                )
            )
    return flags
