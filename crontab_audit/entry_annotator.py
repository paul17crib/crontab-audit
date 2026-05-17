"""Annotate crontab entries with computed metadata labels."""
from dataclasses import dataclass, field
from typing import List, Optional

from crontab_audit.parser import CrontabEntry
from crontab_audit.scheduler import classify_frequency
from crontab_audit.risk import flag_risky_entries


@dataclass
class AnnotatedEntry:
    entry: CrontabEntry
    frequency_label: str
    risk_flags: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        parts = [f"{self.entry.command} [{self.frequency_label}]"]
        if self.risk_flags:
            parts.append(f"risks={','.join(self.risk_flags)}")
        if self.notes:
            parts.append(f"notes={'; '.join(self.notes)}")
        return " | ".join(parts)

    @property
    def is_risky(self) -> bool:
        return len(self.risk_flags) > 0

    @property
    def primary_note(self) -> Optional[str]:
        return self.notes[0] if self.notes else None


def _build_notes(entry: CrontabEntry, frequency_label: str) -> List[str]:
    notes: List[str] = []
    if entry.user and entry.user.lower() == "root":
        notes.append("runs as root")
    if frequency_label == "minutely":
        notes.append("very high frequency")
    if ">/dev/null" in entry.command or "2>&1" in entry.command:
        notes.append("output suppressed")
    return notes


def annotate_entry(entry: CrontabEntry) -> AnnotatedEntry:
    """Annotate a single entry with frequency, risk, and notes."""
    freq = classify_frequency(entry)
    risk_flags = [rf.reason for rf in flag_risky_entries([entry])]
    notes = _build_notes(entry, freq)
    return AnnotatedEntry(
        entry=entry,
        frequency_label=freq,
        risk_flags=risk_flags,
        notes=notes,
    )


def annotate_entries(entries: List[CrontabEntry]) -> List[AnnotatedEntry]:
    """Annotate a list of crontab entries."""
    return [annotate_entry(e) for e in entries]


def filter_annotated(
    annotated: List[AnnotatedEntry],
    risky_only: bool = False,
    frequency: Optional[str] = None,
) -> List[AnnotatedEntry]:
    """Filter annotated entries by risk or frequency label."""
    result = annotated
    if risky_only:
        result = [a for a in result if a.is_risky]
    if frequency:
        result = [a for a in result if a.frequency_label == frequency]
    return result
