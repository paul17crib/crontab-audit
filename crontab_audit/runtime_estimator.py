"""Estimates total daily runtime load per host based on crontab schedules."""

from dataclasses import dataclass, field
from typing import List, Dict
from crontab_audit.parser import CrontabEntry
from crontab_audit.scheduler import classify_frequency

# Estimated average duration (seconds) per frequency label
_DURATION_ESTIMATES: Dict[str, float] = {
    "minutely": 2.0,
    "hourly": 10.0,
    "daily": 30.0,
    "weekly": 60.0,
    "monthly": 120.0,
    "other": 15.0,
}

# Runs per day per frequency label
_RUNS_PER_DAY: Dict[str, float] = {
    "minutely": 1440.0,
    "hourly": 24.0,
    "daily": 1.0,
    "weekly": 1 / 7,
    "monthly": 1 / 30,
    "other": 1.0,
}


@dataclass
class EntryLoadEstimate:
    entry: CrontabEntry
    frequency_label: str
    runs_per_day: float
    estimated_seconds_per_run: float

    @property
    def total_seconds_per_day(self) -> float:
        return self.runs_per_day * self.estimated_seconds_per_run

    def __str__(self) -> str:
        return (
            f"{self.entry.command!r} [{self.frequency_label}] "
            f"~{self.runs_per_day:.1f} runs/day, "
            f"~{self.total_seconds_per_day:.1f}s/day"
        )


@dataclass
class HostLoadReport:
    hostname: str
    estimates: List[EntryLoadEstimate] = field(default_factory=list)

    @property
    def total_seconds_per_day(self) -> float:
        return sum(e.total_seconds_per_day for e in self.estimates)

    @property
    def total_runs_per_day(self) -> float:
        return sum(e.runs_per_day for e in self.estimates)

    def summary_by_frequency(self) -> Dict[str, int]:
        """Return a count of entries grouped by their frequency label."""
        counts: Dict[str, int] = {}
        for estimate in self.estimates:
            counts[estimate.frequency_label] = counts.get(estimate.frequency_label, 0) + 1
        return counts

    def __str__(self) -> str:
        return (
            f"Host: {self.hostname} | "
            f"entries={len(self.estimates)}, "
            f"runs/day~{self.total_runs_per_day:.1f}, "
            f"load~{self.total_seconds_per_day:.1f}s/day"
        )


def estimate_entry_load(entry: CrontabEntry) -> EntryLoadEstimate:
    label = classify_frequency(entry)
    runs = _RUNS_PER_DAY.get(label, 1.0)
    duration = _DURATION_ESTIMATES.get(label, 15.0)
    return EntryLoadEstimate(
        entry=entry,
        frequency_label=label,
        runs_per_day=runs,
        estimated_seconds_per_run=duration,
    )


def build_host_load_report(hostname: str, entries: List[CrontabEntry]) -> HostLoadReport:
    report = HostLoadReport(hostname=hostname)
    for entry in entries:
        report.estimates.append(estimate_entry_load(entry))
    return report


def top_loaded_entries(report: HostLoadReport, n: int = 5) -> List[EntryLoadEstimate]:
    return sorted(report.estimates, key=lambda e: e.total_seconds_per_day, reverse=True)[:n]
