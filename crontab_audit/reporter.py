"""Generates human-readable audit reports from parsed crontab analysis results."""

from dataclasses import dataclass, field
from typing import List

from crontab_audit.parser import CrontabEntry
from crontab_audit.overlap import OverlapResult
from crontab_audit.risk import RiskFlag


@dataclass
class AuditReport:
    host: str
    entries: List[CrontabEntry] = field(default_factory=list)
    risk_flags: List[RiskFlag] = field(default_factory=list)
    overlaps: List[OverlapResult] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"=== Crontab Audit Report: {self.host} ===",
            f"Total entries : {len(self.entries)}",
            f"Risk flags    : {len(self.risk_flags)}",
            f"Overlaps      : {len(self.overlaps)}",
        ]
        return "\n".join(lines)

    def detailed(self) -> str:
        sections = [self.summary()]

        if self.risk_flags:
            sections.append("\n-- Risk Flags --")
            for rf in self.risk_flags:
                sections.append(f"  {rf}")

        if self.overlaps:
            sections.append("\n-- Schedule Overlaps --")
            for ov in self.overlaps:
                sections.append(f"  {ov}")

        if not self.risk_flags and not self.overlaps:
            sections.append("\nNo issues found.")

        return "\n".join(sections)

    def has_issues(self) -> bool:
        return bool(self.risk_flags or self.overlaps)


def build_report(host: str, entries: List[CrontabEntry]) -> AuditReport:
    """Build a full AuditReport for a host given its parsed entries."""
    from crontab_audit.risk import flag_risky_entries
    from crontab_audit.overlap import find_overlaps

    risk_flags = flag_risky_entries(entries)
    overlaps = find_overlaps(entries)
    return AuditReport(
        host=host,
        entries=entries,
        risk_flags=risk_flags,
        overlaps=overlaps,
    )
