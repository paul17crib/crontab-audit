"""Formats ChangeReport output for display."""
from crontab_audit.change_tracker import ChangeReport, EntryChange
from typing import List


def _format_entry_change(change: EntryChange) -> str:
    entry = change.new_entry or change.old_entry
    if entry is None:
        return f"  [{change.change_type.upper()}] {change.host}: (unknown)"
    schedule = " ".join(entry.schedule_fields)
    return f"  [{change.change_type.upper()}] {change.host}: {schedule}  {entry.command}"


def format_change_report(report: ChangeReport) -> str:
    if not report.has_changes:
        return "No changes detected."

    lines = ["Crontab Changes Detected:", ""]

    if report.added:
        lines.append(f"Added ({len(report.added)}):")
        for c in report.added:
            lines.append(_format_entry_change(c))
        lines.append("")

    if report.removed:
        lines.append(f"Removed ({len(report.removed)}):")
        for c in report.removed:
            lines.append(_format_entry_change(c))
        lines.append("")

    lines.append(report.summary())
    return "\n".join(lines)


def format_change_summary(report: ChangeReport) -> str:
    return report.summary()


def format_changes_by_host(report: ChangeReport) -> str:
    if not report.has_changes:
        return "No changes detected."

    by_host: dict = {}
    for change in report.changes:
        by_host.setdefault(change.host, []).append(change)

    lines = []
    for host in sorted(by_host):
        lines.append(f"{host}:")
        for c in by_host[host]:
            lines.append(_format_entry_change(c))
        lines.append("")

    return "\n".join(lines).rstrip()
