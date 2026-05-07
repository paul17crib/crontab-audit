"""Formats runtime load estimates for display."""

from typing import List
from crontab_audit.runtime_estimator import HostLoadReport, EntryLoadEstimate, top_loaded_entries


def format_entry_estimate(est: EntryLoadEstimate) -> str:
    return (
        f"  [{est.frequency_label:10s}] "
        f"{est.runs_per_day:7.1f} runs/day  "
        f"{est.total_seconds_per_day:8.1f}s/day  "
        f"{est.entry.command}"
    )


def format_host_load(report: HostLoadReport, top_n: int = 0) -> str:
    lines = [f"=== {report.hostname} ==="]
    lines.append(
        f"  Total: {len(report.estimates)} entries, "
        f"~{report.total_runs_per_day:.1f} runs/day, "
        f"~{report.total_seconds_per_day:.1f}s/day estimated load"
    )
    entries = top_loaded_entries(report, top_n) if top_n > 0 else report.estimates
    if entries:
        lines.append(f"  {'Frequency':<10}  {'Runs/Day':>9}  {'Load(s/day)':>11}  Command")
        lines.append("  " + "-" * 60)
        for est in entries:
            lines.append(format_entry_estimate(est))
    return "\n".join(lines)


def format_all_hosts_load(reports: List[HostLoadReport], top_n: int = 0) -> str:
    if not reports:
        return "No host load data available."
    return "\n\n".join(format_host_load(r, top_n=top_n) for r in reports)


def format_load_summary(reports: List[HostLoadReport]) -> str:
    if not reports:
        return "No hosts to summarise."
    lines = ["Runtime Load Summary", "=" * 40]
    total_entries = sum(len(r.estimates) for r in reports)
    total_runs = sum(r.total_runs_per_day for r in reports)
    total_load = sum(r.total_seconds_per_day for r in reports)
    lines.append(f"Hosts   : {len(reports)}")
    lines.append(f"Entries : {total_entries}")
    lines.append(f"Runs/day: ~{total_runs:.1f}")
    lines.append(f"Load/day: ~{total_load:.1f}s")
    lines.append("")
    sorted_reports = sorted(reports, key=lambda r: r.total_seconds_per_day, reverse=True)
    lines.append(f"  {'Host':<30} {'Runs/day':>10} {'Load(s/day)':>12}")
    lines.append("  " + "-" * 55)
    for r in sorted_reports:
        lines.append(f"  {r.hostname:<30} {r.total_runs_per_day:>10.1f} {r.total_seconds_per_day:>12.1f}")
    return "\n".join(lines)
