"""Aggregate statistics across all crontab entries."""
from __future__ import annotations

from dataclasses import dataclass, field
from collections import Counter
from typing import List, Dict

from crontab_audit.parser import CrontabEntry
from crontab_audit.scheduler import classify_frequency


@dataclass
class EntryStats:
    total_entries: int = 0
    entries_with_user: int = 0
    entries_with_host: int = 0
    frequency_counts: Dict[str, int] = field(default_factory=dict)
    top_commands: List[tuple] = field(default_factory=list)
    host_counts: Dict[str, int] = field(default_factory=dict)
    user_counts: Dict[str, int] = field(default_factory=dict)

    def __str__(self) -> str:
        lines = [
            f"Total entries : {self.total_entries}",
            f"With user     : {self.entries_with_user}",
            f"With host     : {self.entries_with_host}",
        ]
        if self.frequency_counts:
            lines.append("Frequencies   :")
            for label, count in sorted(self.frequency_counts.items()):
                lines.append(f"  {label:<14} {count}")
        if self.top_commands:
            lines.append("Top commands  :")
            for cmd, count in self.top_commands[:5]:
                lines.append(f"  {count:>4}x  {cmd}")
        return "\n".join(lines)


def _command_key(entry: CrontabEntry) -> str:
    parts = entry.command.split()
    if not parts:
        return ""
    token = parts[0]
    if "=" in token and len(parts) > 1:
        return parts[1]
    return token


def compute_entry_stats(entries: List[CrontabEntry], top_n: int = 10) -> EntryStats:
    """Compute aggregate statistics for a list of CrontabEntry objects."""
    if not entries:
        return EntryStats()

    freq_counter: Counter = Counter()
    cmd_counter: Counter = Counter()
    host_counter: Counter = Counter()
    user_counter: Counter = Counter()

    entries_with_user = 0
    entries_with_host = 0

    for entry in entries:
        freq_label = classify_frequency(entry)
        freq_counter[freq_label] += 1
        cmd_counter[_command_key(entry)] += 1

        if entry.user:
            entries_with_user += 1
            user_counter[entry.user] += 1

        if entry.host:
            entries_with_host += 1
            host_counter[entry.host] += 1

    return EntryStats(
        total_entries=len(entries),
        entries_with_user=entries_with_user,
        entries_with_host=entries_with_host,
        frequency_counts=dict(freq_counter),
        top_commands=cmd_counter.most_common(top_n),
        host_counts=dict(host_counter),
        user_counts=dict(user_counter),
    )
