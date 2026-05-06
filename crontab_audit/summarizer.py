"""Summarizes audit results across multiple hosts into aggregated statistics."""

from dataclasses import dataclass, field
from typing import Dict, List
from crontab_audit.loader import HostCrontab
from crontab_audit.reporter import AuditReport, build_report
from crontab_audit.risk import flag_risky_entries
from crontab_audit.overlap import find_overlaps


@dataclass
class HostSummaryStats:
    hostname: str
    total_entries: int
    risky_count: int
    overlap_count: int
    parse_error_count: int
    risk_commands: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        return (
            f"[{self.hostname}] entries={self.total_entries} "
            f"risky={self.risky_count} overlaps={self.overlap_count} "
            f"parse_errors={self.parse_error_count}"
        )


@dataclass
class MultiHostSummary:
    host_stats: List[HostSummaryStats] = field(default_factory=list)

    @property
    def total_hosts(self) -> int:
        return len(self.host_stats)

    @property
    def total_entries(self) -> int:
        return sum(s.total_entries for s in self.host_stats)

    @property
    def total_risky(self) -> int:
        return sum(s.risky_count for s in self.host_stats)

    @property
    def total_overlaps(self) -> int:
        return sum(s.overlap_count for s in self.host_stats)

    @property
    def total_parse_errors(self) -> int:
        return sum(s.parse_error_count for s in self.host_stats)

    @property
    def hosts_with_issues(self) -> List[str]:
        return [
            s.hostname
            for s in self.host_stats
            if s.risky_count > 0 or s.overlap_count > 0 or s.parse_error_count > 0
        ]

    def by_hostname(self) -> Dict[str, HostSummaryStats]:
        return {s.hostname: s for s in self.host_stats}


def summarize_host(host: HostCrontab) -> HostSummaryStats:
    """Compute summary statistics for a single host."""
    risk_flags = flag_risky_entries(host.entries)
    overlaps = find_overlaps(host.entries)
    report: AuditReport = build_report(host.entries, risk_flags, overlaps)

    risky_commands = [
        f.entry.command for f in risk_flags
    ]

    return HostSummaryStats(
        hostname=host.hostname,
        total_entries=len(host.entries),
        risky_count=len(report.risk_flags),
        overlap_count=len(report.overlaps),
        parse_error_count=len(host.parse_errors),
        risk_commands=risky_commands,
    )


def summarize_all(hosts: List[HostCrontab]) -> MultiHostSummary:
    """Aggregate summary statistics across all hosts."""
    return MultiHostSummary(
        host_stats=[summarize_host(h) for h in hosts]
    )
