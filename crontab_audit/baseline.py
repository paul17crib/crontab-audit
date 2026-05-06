"""Baseline comparison: compare current crontab state against a saved baseline."""

from dataclasses import dataclass, field
from typing import List, Optional

from crontab_audit.loader import HostCrontab
from crontab_audit.snapshot import save_snapshot, load_snapshot
from crontab_audit.differ import diff_host, CrontabDiff


@dataclass
class BaselineReport:
    """Result of comparing current host crontabs against a baseline snapshot."""
    diffs: List[CrontabDiff] = field(default_factory=list)
    new_hosts: List[str] = field(default_factory=list)
    removed_hosts: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return (
            bool(self.new_hosts)
            or bool(self.removed_hosts)
            or any(d.has_changes for d in self.diffs)
        )

    def summary(self) -> str:
        lines = []
        if self.new_hosts:
            lines.append(f"New hosts: {', '.join(self.new_hosts)}")
        if self.removed_hosts:
            lines.append(f"Removed hosts: {', '.join(self.removed_hosts)}")
        for diff in self.diffs:
            if diff.has_changes:
                lines.append(str(diff))
        if not lines:
            return "No changes detected against baseline."
        return "\n".join(lines)


def compare_against_baseline(
    current_hosts: List[HostCrontab],
    baseline_path: str,
) -> Optional[BaselineReport]:
    """Load a baseline snapshot and diff each host against it.

    Returns None if no baseline snapshot exists yet.
    """
    baseline_data = load_snapshot(baseline_path)
    if baseline_data is None:
        return None

    baseline_map = {hc["hostname"]: hc for hc in baseline_data}
    current_map = {hc.hostname: hc for hc in current_hosts}

    report = BaselineReport()
    report.new_hosts = [h for h in current_map if h not in baseline_map]
    report.removed_hosts = [h for h in baseline_map if h not in current_map]

    for hostname, host_crontab in current_map.items():
        if hostname not in baseline_map:
            continue
        old_entries_raw = baseline_map[hostname].get("entries", [])
        # Reconstruct a minimal HostCrontab-like object from snapshot dict
        from crontab_audit.snapshot import _entry_from_dict
        from crontab_audit.loader import HostCrontab as HC
        old_entries = [_entry_from_dict(e) for e in old_entries_raw]
        old_host = HC(hostname=hostname, entries=old_entries, parse_errors=[])
        report.diffs.append(diff_host(old_host, host_crontab))

    return report


def save_baseline(current_hosts: List[HostCrontab], baseline_path: str) -> None:
    """Persist current crontab state as the new baseline snapshot."""
    save_snapshot(current_hosts, baseline_path)
