"""Whitelist support: skip known-safe entries from audit results."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List

from crontab_audit.parser import CrontabEntry


@dataclass
class WhitelistEntry:
    """A pattern that marks a crontab entry as known-safe."""
    command_contains: str = ""
    schedule_exact: str = ""
    host: str = ""
    reason: str = ""

    def matches(self, entry: CrontabEntry) -> bool:
        if self.host and entry.host != self.host:
            return False
        if self.schedule_exact:
            if str(entry.schedule_fields) != self.schedule_exact:
                return False
        if self.command_contains:
            if self.command_contains not in entry.command:
                return False
        return bool(self.command_contains or self.schedule_exact)


@dataclass
class Whitelist:
    entries: List[WhitelistEntry] = field(default_factory=list)

    def is_whitelisted(self, entry: CrontabEntry) -> bool:
        return any(w.matches(entry) for w in self.entries)

    def filter(self, entries: Iterable[CrontabEntry]) -> List[CrontabEntry]:
        return [e for e in entries if not self.is_whitelisted(e)]


def load_whitelist(path: str | Path) -> Whitelist:
    """Load a whitelist from a JSON file."""
    data = json.loads(Path(path).read_text())
    entries = [
        WhitelistEntry(
            command_contains=item.get("command_contains", ""),
            schedule_exact=item.get("schedule_exact", ""),
            host=item.get("host", ""),
            reason=item.get("reason", ""),
        )
        for item in data.get("whitelist", [])
    ]
    return Whitelist(entries=entries)


def save_whitelist(whitelist: Whitelist, path: str | Path) -> None:
    """Persist a whitelist to a JSON file."""
    data = {
        "whitelist": [
            {
                "command_contains": e.command_contains,
                "schedule_exact": e.schedule_exact,
                "host": e.host,
                "reason": e.reason,
            }
            for e in whitelist.entries
        ]
    }
    Path(path).write_text(json.dumps(data, indent=2))
