"""Scores individual crontab entries based on risk, frequency, and complexity."""

from dataclasses import dataclass, field
from typing import List

from crontab_audit.parser import CrontabEntry
from crontab_audit.risk import flag_risky_entries
from crontab_audit.scheduler import classify_frequency
from crontab_audit.pattern_matcher import match_entry


@dataclass
class EntryScore:
    entry: CrontabEntry
    risk_score: int
    frequency_score: int
    complexity_score: int
    notes: List[str] = field(default_factory=list)

    @property
    def total_score(self) -> int:
        return self.risk_score + self.frequency_score + self.complexity_score

    @property
    def grade(self) -> str:
        if self.total_score >= 15:
            return "F"
        if self.total_score >= 10:
            return "D"
        if self.total_score >= 6:
            return "C"
        if self.total_score >= 3:
            return "B"
        return "A"

    def __str__(self) -> str:
        cmd = self.entry.command[:40]
        return (
            f"[{self.grade}] score={self.total_score} "
            f"(risk={self.risk_score}, freq={self.frequency_score}, "
            f"complexity={self.complexity_score}) | {cmd}"
        )


_FREQUENCY_SCORES = {
    "minutely": 5,
    "hourly": 3,
    "daily": 1,
    "weekly": 1,
    "monthly": 0,
    "unknown": 1,
}


def _complexity_score(entry: CrontabEntry) -> tuple:
    """Return (score, notes) based on command complexity."""
    score = 0
    notes = []
    cmd = entry.command
    if "|" in cmd:
        score += 2
        notes.append("pipe detected")
    if "&&" in cmd or "||" in cmd:
        score += 1
        notes.append("chained commands")
    if ";" in cmd:
        score += 1
        notes.append("semicolon chain")
    if len(cmd) > 120:
        score += 1
        notes.append("long command")
    return score, notes


def score_entry(entry: CrontabEntry) -> EntryScore:
    notes: List[str] = []

    risk_flags = flag_risky_entries([entry])
    risk_score = len(risk_flags) * 3
    for f in risk_flags:
        notes.append(f"risk: {f.reason}")

    matches = match_entry(entry)
    risk_score += len(matches) * 2
    for m in matches:
        notes.append(f"pattern: {m.pattern_name}")

    freq_label = classify_frequency(entry)
    frequency_score = _FREQUENCY_SCORES.get(freq_label, 1)
    notes.append(f"frequency: {freq_label}")

    comp_score, comp_notes = _complexity_score(entry)
    notes.extend(comp_notes)

    return EntryScore(
        entry=entry,
        risk_score=risk_score,
        frequency_score=frequency_score,
        complexity_score=comp_score,
        notes=notes,
    )


def score_entries(entries: List[CrontabEntry]) -> List[EntryScore]:
    return [score_entry(e) for e in entries]
