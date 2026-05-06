"""Host health scoring: assigns a numeric health score to each host based on
risk flags, overlaps, duplicates, stale entries, and parse errors."""

from dataclasses import dataclass, field
from typing import List

from crontab_audit.loader import HostCrontab
from crontab_audit.risk import flag_risky_entries
from crontab_audit.overlap import find_overlaps
from crontab_audit.duplicate_detector import find_duplicates
from crontab_audit.stale_detector import find_stale_entries

# Penalty weights
_PENALTY_RISK = 10
_PENALTY_OVERLAP = 5
_PENALTY_DUPLICATE = 4
_PENALTY_STALE = 3
_PENALTY_PARSE_ERROR = 6
_MAX_SCORE = 100


@dataclass
class HostHealthScore:
    hostname: str
    score: int  # 0 (worst) – 100 (perfect)
    risk_count: int
    overlap_count: int
    duplicate_count: int
    stale_count: int
    parse_error_count: int
    penalties: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        grade = _grade(self.score)
        return (
            f"{self.hostname}: score={self.score}/100 [{grade}] "
            f"(risks={self.risk_count}, overlaps={self.overlap_count}, "
            f"duplicates={self.duplicate_count}, stale={self.stale_count}, "
            f"parse_errors={self.parse_error_count})"
        )


def _grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 55:
        return "C"
    if score >= 35:
        return "D"
    return "F"


def score_host(host: HostCrontab) -> HostHealthScore:
    """Compute a health score for a single host."""
    entries = host.entries

    risks = flag_risky_entries(entries)
    overlaps = find_overlaps(entries)
    duplicates = find_duplicates(entries)
    stale = find_stale_entries(entries)
    parse_errors = len(host.parse_errors)

    risk_count = len(risks)
    overlap_count = len(overlaps)
    duplicate_count = len(duplicates)
    stale_count = len(stale)

    total_penalty = (
        risk_count * _PENALTY_RISK
        + overlap_count * _PENALTY_OVERLAP
        + duplicate_count * _PENALTY_DUPLICATE
        + stale_count * _PENALTY_STALE
        + parse_errors * _PENALTY_PARSE_ERROR
    )

    score = max(0, _MAX_SCORE - total_penalty)

    penalties = []
    if risk_count:
        penalties.append(f"{risk_count} risky command(s)")
    if overlap_count:
        penalties.append(f"{overlap_count} schedule overlap(s)")
    if duplicate_count:
        penalties.append(f"{duplicate_count} duplicate(s)")
    if stale_count:
        penalties.append(f"{stale_count} stale entry/entries")
    if parse_errors:
        penalties.append(f"{parse_errors} parse error(s)")

    return HostHealthScore(
        hostname=host.hostname,
        score=score,
        risk_count=risk_count,
        overlap_count=overlap_count,
        duplicate_count=duplicate_count,
        stale_count=stale_count,
        parse_error_count=parse_errors,
        penalties=penalties,
    )


def score_all_hosts(hosts: List[HostCrontab]) -> List[HostHealthScore]:
    """Score every host, sorted best-to-worst."""
    scores = [score_host(h) for h in hosts]
    scores.sort(key=lambda s: s.score, reverse=True)
    return scores
