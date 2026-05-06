"""Diff crontab entries between two snapshots of host crontabs."""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from crontab_audit.loader import HostCrontab
from crontab_audit.parser import CrontabEntry


@dataclass
class CrontabDiff:
    hostname: str
    added: List[CrontabEntry] = field(default_factory=list)
    removed: List[CrontabEntry] = field(default_factory=list)
    unchanged: List[CrontabEntry] = field(default_factory=list)

    def has_changes(self) -> bool:
        return bool(self.added or self.removed)

    def __str__(self) -> str:
        lines = [f"Diff for {self.hostname}:"]
        for e in self.added:
            lines.append(f"  + {e}")
        for e in self.removed:
            lines.append(f"  - {e}")
        if not self.has_changes():
            lines.append("  (no changes)")
        return "\n".join(lines)


def _entry_key(entry: CrontabEntry) -> Tuple[str, str]:
    """Unique key for an entry based on schedule and command."""
    schedule = " ".join([
        entry.minute, entry.hour, entry.day_of_month,
        entry.month, entry.day_of_week
    ])
    return (schedule, entry.command)


def diff_host(before: HostCrontab, after: HostCrontab) -> CrontabDiff:
    """Compare two HostCrontab snapshots for the same host."""
    before_keys: Dict[Tuple[str, str], CrontabEntry] = {
        _entry_key(e): e for e in before.entries
    }
    after_keys: Dict[Tuple[str, str], CrontabEntry] = {
        _entry_key(e): e for e in after.entries
    }

    added = [after_keys[k] for k in after_keys if k not in before_keys]
    removed = [before_keys[k] for k in before_keys if k not in after_keys]
    unchanged = [before_keys[k] for k in before_keys if k in after_keys]

    return CrontabDiff(
        hostname=after.hostname,
        added=added,
        removed=removed,
        unchanged=unchanged,
    )


def diff_all(
    before_hosts: List[HostCrontab],
    after_hosts: List[HostCrontab],
) -> List[CrontabDiff]:
    """Diff all hosts between two sets of HostCrontab snapshots."""
    before_map = {h.hostname: h for h in before_hosts}
    after_map = {h.hostname: h for h in after_hosts}

    all_hostnames = set(before_map) | set(after_map)
    results = []

    for hostname in sorted(all_hostnames):
        empty = HostCrontab(hostname=hostname, entries=[], parse_errors=[])
        before = before_map.get(hostname, empty)
        after = after_map.get(hostname, empty)
        results.append(diff_host(before, after))

    return results
