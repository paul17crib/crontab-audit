"""Tracks changes to crontab entries over time, comparing current state to a saved baseline."""
from dataclasses import dataclass, field
from typing import List, Optional
from crontab_audit.loader import HostCrontab
from crontab_audit.parser import CrontabEntry


@dataclass
class EntryChange:
    host: str
    change_type: str  # 'added', 'removed', 'modified'
    old_entry: Optional[CrontabEntry] = None
    new_entry: Optional[CrontabEntry] = None

    def __str__(self) -> str:
        entry = self.new_entry or self.old_entry
        cmd = entry.command if entry else "unknown"
        return f"[{self.change_type.upper()}] {self.host}: {cmd}"


@dataclass
class ChangeReport:
    changes: List[EntryChange] = field(default_factory=list)

    @property
    def added(self) -> List[EntryChange]:
        return [c for c in self.changes if c.change_type == "added"]

    @property
    def removed(self) -> List[EntryChange]:
        return [c for c in self.changes if c.change_type == "removed"]

    @property
    def has_changes(self) -> bool:
        return len(self.changes) > 0

    def summary(self) -> str:
        return (
            f"Changes: {len(self.changes)} total "
            f"({len(self.added)} added, {len(self.removed)} removed)"
        )


def _entry_key(entry: CrontabEntry) -> str:
    schedule = " ".join(entry.schedule_fields)
    return f"{schedule}|{entry.command.strip()}"


def track_changes(
    old_hosts: List[HostCrontab],
    new_hosts: List[HostCrontab],
) -> ChangeReport:
    old_map = {h.hostname: h for h in old_hosts}
    new_map = {h.hostname: h for h in new_hosts}
    all_hosts = set(old_map) | set(new_map)
    report = ChangeReport()

    for hostname in sorted(all_hosts):
        old_entries = {_entry_key(e): e for e in (old_map[hostname].entries if hostname in old_map else [])}
        new_entries = {_entry_key(e): e for e in (new_map[hostname].entries if hostname in new_map else [])}

        for key, entry in new_entries.items():
            if key not in old_entries:
                report.changes.append(EntryChange(host=hostname, change_type="added", new_entry=entry))

        for key, entry in old_entries.items():
            if key not in new_entries:
                report.changes.append(EntryChange(host=hostname, change_type="removed", old_entry=entry))

    return report
