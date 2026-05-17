"""Formatters for entry scoring results."""

from typing import List

from crontab_audit.entry_scorer import EntryScore


def format_score_row(score: EntryScore) -> str:
    host = score.entry.host or "unknown"
    cmd = score.entry.command[:50]
    return (
        f"  [{score.grade}] total={score.total_score:>3} "
        f"risk={score.risk_score} freq={score.frequency_score} "
        f"complex={score.complexity_score}  "
        f"host={host}  cmd={cmd}"
    )


def format_score_report(scores: List[EntryScore], top_n: int = 0) -> str:
    if not scores:
        return "No entries to score."

    sorted_scores = sorted(scores, key=lambda s: s.total_score, reverse=True)
    if top_n > 0:
        sorted_scores = sorted_scores[:top_n]

    lines = ["Entry Score Report", "=" * 60]
    for s in sorted_scores:
        lines.append(format_score_row(s))
        for note in s.notes:
            lines.append(f"       - {note}")
    return "\n".join(lines)


def format_score_summary(scores: List[EntryScore]) -> str:
    if not scores:
        return "No entries scored."

    grade_counts: dict = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
    for s in scores:
        grade_counts[s.grade] = grade_counts.get(s.grade, 0) + 1

    avg = sum(s.total_score for s in scores) / len(scores)
    worst = max(scores, key=lambda s: s.total_score)

    lines = [
        f"Scored {len(scores)} entries  avg={avg:.1f}",
        "  Grades: " + "  ".join(f"{g}={grade_counts[g]}" for g in "ABCDF"),
        f"  Worst: [{worst.grade}] score={worst.total_score} | {worst.entry.command[:50]}",
    ]
    return "\n".join(lines)


def format_scores_by_grade(scores: List[EntryScore]) -> str:
    if not scores:
        return "No entries scored."

    groups: dict = {g: [] for g in "ABCDF"}
    for s in scores:
        groups[s.grade].append(s)

    lines = ["Entries by Grade", "=" * 40]
    for grade in "FABCDE"[::-1][1:]:
        group = groups.get(grade, [])
        if not group:
            continue
        lines.append(f"\nGrade {grade} ({len(group)} entries):")
        for s in group:
            lines.append(format_score_row(s))
    return "\n".join(lines)
