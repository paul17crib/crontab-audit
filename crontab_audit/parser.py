"""Parses raw crontab lines into structured CrontabEntry objects."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CrontabEntry:
    host: str
    raw_line: str
    minute: str
    hour: str
    day_of_month: str
    month: str
    day_of_week: str
    command: str
    line_number: Optional[int] = None
    comment: str = ""

    def schedule_fields(self) -> tuple:
        return (self.minute, self.hour, self.day_of_month, self.month, self.day_of_week)

    def __str__(self) -> str:
        return (
            f"[{self.host}:{self.line_number}] "
            f"{' '.join(self.schedule_fields())} {self.command}"
        )


class CrontabParseError(ValueError):
    pass


def parse_line(line: str, host: str, line_number: int = None) -> Optional[CrontabEntry]:
    """Parse a single crontab line. Returns None for blank/comment lines."""
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None

    # Strip inline comment
    comment = ""
    if " #" in stripped:
        stripped, comment = stripped.split(" #", 1)
        comment = comment.strip()

    parts = stripped.split()
    if len(parts) < 6:
        raise CrontabParseError(
            f"Invalid crontab entry on line {line_number} for host '{host}': '{line.strip()}'"
        )

    minute, hour, dom, month, dow = parts[:5]
    command = " ".join(parts[5:])

    return CrontabEntry(
        host=host,
        raw_line=line.rstrip(),
        minute=minute,
        hour=hour,
        day_of_month=dom,
        month=month,
        day_of_week=dow,
        command=command,
        line_number=line_number,
        comment=comment,
    )


def parse_crontab(content: str, host: str) -> list[CrontabEntry]:
    """Parse a full crontab file content for a given host."""
    entries = []
    for lineno, line in enumerate(content.splitlines(), start=1):
        entry = parse_line(line, host=host, line_number=lineno)
        if entry is not None:
            entries.append(entry)
    return entries
