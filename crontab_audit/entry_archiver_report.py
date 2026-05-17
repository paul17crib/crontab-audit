"""Formatting helpers for entry archive records."""

from typing import List, Optional

from crontab_audit.entry_archiver import ArchiveRecord


def format_archive_records(
    records: List[ArchiveRecord],
    verbose: bool = False,
) -> str:
    if not records:
        return "No archived entries found."
    lines = [f"Archived entries ({len(records)} total):", ""]
    for r in records:
        lines.append(f"  {r.archived_at}  {r.schedule:<20}  {r.command}")
        if verbose:
            host_str = r.host or "(unknown)"
            user_str = r.user or "(unknown)"
            lines.append(f"    host={host_str}  user={user_str}")
    return "\n".join(lines)


def format_archive_summary(records: List[ArchiveRecord]) -> str:
    if not records:
        return "Archive is empty."
    hosts = {r.host for r in records if r.host}
    timestamps = sorted({r.archived_at for r in records})
    lines = [
        f"Total archived records : {len(records)}",
        f"Distinct hosts         : {len(hosts)}",
        f"Earliest snapshot      : {timestamps[0]}",
        f"Latest snapshot        : {timestamps[-1]}",
    ]
    return "\n".join(lines)


def format_archive_by_host(records: List[ArchiveRecord]) -> str:
    if not records:
        return "No archived entries found."
    grouped: dict = {}
    for r in records:
        key = r.host or "(unknown)"
        grouped.setdefault(key, []).append(r)

    lines: List[str] = []
    for host in sorted(grouped):
        host_records = grouped[host]
        lines.append(f"Host: {host} ({len(host_records)} entries)")
        for r in host_records:
            lines.append(f"  {r.archived_at}  {r.schedule:<20}  {r.command}")
        lines.append("")
    return "\n".join(lines).rstrip()
