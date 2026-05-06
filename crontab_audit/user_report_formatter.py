"""Formats UserReport data for display."""

from __future__ import annotations

from typing import List

from crontab_audit.user_tracker import UserReport, UserStats


def format_user_stats(stats: UserStats) -> str:
    lines = [f"  User: {stats.username}"]
    lines.append(f"    Entries : {len(stats.entries)}")
    lines.append(f"    Hosts   : {', '.join(sorted(set(stats.hosts))) or 'unknown'}")
    return "\n".join(lines)


def format_user_report(report: UserReport, top_n: int = 0) -> str:
    """Return a formatted string for all users or the top N by entry count."""
    if not report.stats:
        return "No user data available."

    users: List[UserStats] = (
        report.top_users(top_n) if top_n > 0 else list(report.stats.values())
    )
    users = sorted(users, key=lambda s: (-len(s.entries), s.username))

    lines = [f"User Report ({len(users)} user(s)):", "-" * 40]
    for stats in users:
        lines.append(format_user_stats(stats))
    lines.append("-" * 40)
    lines.append(f"Total users: {report.total_users()}")
    return "\n".join(lines)


def format_users_per_host(report: UserReport) -> str:
    """Show which users appear on each host."""
    host_to_users: dict = {}
    for username, stats in report.stats.items():
        for host in stats.hosts:
            host_to_users.setdefault(host, []).append(username)

    if not host_to_users:
        return "No host/user data available."

    lines = ["Users per host:", "-" * 40]
    for host in sorted(host_to_users):
        users_str = ", ".join(sorted(host_to_users[host]))
        lines.append(f"  {host}: {users_str}")
    return "\n".join(lines)
