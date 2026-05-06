"""Tracks which user owns each crontab entry and reports per-user statistics."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List

from crontab_audit.parser import CrontabEntry


@dataclass
class UserStats:
    username: str
    entries: List[CrontabEntry] = field(default_factory=list)
    hosts: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        host_list = ", ".join(sorted(set(self.hosts))) or "unknown"
        return (
            f"User '{self.username}': {len(self.entries)} entries "
            f"across hosts: {host_list}"
        )


@dataclass
class UserReport:
    stats: Dict[str, UserStats] = field(default_factory=dict)

    def total_users(self) -> int:
        return len(self.stats)

    def top_users(self, n: int = 5) -> List[UserStats]:
        sorted_stats = sorted(
            self.stats.values(), key=lambda s: len(s.entries), reverse=True
        )
        return sorted_stats[:n]

    def users_on_host(self, hostname: str) -> List[str]:
        return [
            username
            for username, stats in self.stats.items()
            if hostname in stats.hosts
        ]


def build_user_report(entries: List[CrontabEntry]) -> UserReport:
    """Aggregate entries by the 'user' attribute on CrontabEntry (may be None)."""
    buckets: Dict[str, UserStats] = defaultdict(lambda: UserStats(username=""))

    for entry in entries:
        username = getattr(entry, "user", None) or "unknown"
        if username not in buckets:
            buckets[username] = UserStats(username=username)
        buckets[username].entries.append(entry)
        hostname = getattr(entry, "host", None) or "unknown"
        if hostname not in buckets[username].hosts:
            buckets[username].hosts.append(hostname)

    return UserReport(stats=dict(buckets))
