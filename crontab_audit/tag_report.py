"""Tag-aware reporting utilities.

Builds per-tag summaries and integrates with the existing AuditReport
to provide tag-scoped views of risk and overlap findings.
"""

from dataclasses import dataclass, field
from typing import Dict, List

from crontab_audit.parser import CrontabEntry
from crontab_audit.tag_filter import extract_tags, group_by_tag
from crontab_audit.risk import flag_risky_entries, RiskFlag
from crontab_audit.reporter import AuditReport


@dataclass
class TagSummary:
    """Summary statistics for a single tag group."""

    tag: str
    entry_count: int
    risky_count: int
    entries: List[CrontabEntry] = field(default_factory=list)
    risk_flags: List[RiskFlag] = field(default_factory=list)

    def __str__(self) -> str:
        return (
            f"[{self.tag}] entries={self.entry_count} "
            f"risky={self.risky_count}"
        )


def build_tag_summaries(
    entries: List[CrontabEntry],
) -> Dict[str, TagSummary]:
    """Build a TagSummary for every tag found across the given entries.

    Args:
        entries: All CrontabEntry objects to analyse.

    Returns:
        Mapping of tag name -> TagSummary.
    """
    groups = group_by_tag(entries)
    summaries: Dict[str, TagSummary] = {}

    for tag, tag_entries in groups.items():
        flags = flag_risky_entries(tag_entries)
        risky_commands = {f.entry.command for f in flags}
        risky_count = sum(
            1 for e in tag_entries if e.command in risky_commands
        )
        summaries[tag] = TagSummary(
            tag=tag,
            entry_count=len(tag_entries),
            risky_count=risky_count,
            entries=tag_entries,
            risk_flags=flags,
        )

    return summaries


def format_tag_report(summaries: Dict[str, TagSummary]) -> str:
    """Format tag summaries into a human-readable report string.

    Args:
        summaries: Mapping returned by build_tag_summaries.

    Returns:
        Multi-line string suitable for console output.
    """
    if not summaries:
        return "No tagged entries found."

    lines = ["=== Tag Report ==="]
    for tag in sorted(summaries):
        s = summaries[tag]
        lines.append(str(s))
        if s.risk_flags:
            for flag in s.risk_flags:
                lines.append(f"  RISK  {flag}")
    return "\n".join(lines)
