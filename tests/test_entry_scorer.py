"""Tests for entry_scorer and entry_scorer_report."""

import pytest
from crontab_audit.parser import CrontabEntry
from crontab_audit.entry_scorer import (
    score_entry,
    score_entries,
    EntryScore,
    _complexity_score,
)
from crontab_audit.entry_scorer_report import (
    format_score_report,
    format_score_summary,
    format_scores_by_grade,
)


def make_entry(command="echo hello", minute="0", hour="9",
               dom="*", month="*", dow="*",
               host="host1", user=None):
    return CrontabEntry(
        minute=minute, hour=hour, dom=dom,
        month=month, dow=dow, command=command,
        host=host, user=user,
    )


def test_score_entry_returns_entry_score():
    e = make_entry()
    result = score_entry(e)
    assert isinstance(result, EntryScore)
    assert result.entry is e


def test_score_safe_entry_grade_a():
    e = make_entry(command="echo hello", minute="0", hour="9")
    result = score_entry(e)
    assert result.grade == "A"
    assert result.total_score < 3


def test_score_risky_command_raises_risk_score():
    e = make_entry(command="rm -rf /var/tmp")
    result = score_entry(e)
    assert result.risk_score > 0


def test_score_minutely_raises_frequency_score():
    e = make_entry(command="echo ping", minute="*", hour="*")
    result = score_entry(e)
    assert result.frequency_score >= 5


def test_score_pipe_raises_complexity():
    e = make_entry(command="cat /etc/passwd | grep root")
    result = score_entry(e)
    assert result.complexity_score >= 2


def test_score_chained_commands_raises_complexity():
    e = make_entry(command="cmd1 && cmd2 || fallback")
    result = score_entry(e)
    assert result.complexity_score >= 2


def test_complexity_score_semicolon():
    e = make_entry(command="cmd1; cmd2")
    score, notes = _complexity_score(e)
    assert score >= 1
    assert any("semicolon" in n for n in notes)


def test_complexity_score_long_command():
    e = make_entry(command="x" * 130)
    score, notes = _complexity_score(e)
    assert any("long" in n for n in notes)


def test_score_entries_returns_list():
    entries = [make_entry(), make_entry(command="wget http://example.com")]
    results = score_entries(entries)
    assert len(results) == 2
    assert all(isinstance(r, EntryScore) for r in results)


def test_notes_include_frequency_label():
    e = make_entry(minute="0", hour="*")
    result = score_entry(e)
    assert any("frequency" in n for n in result.notes)


def test_format_score_report_empty():
    assert "No entries" in format_score_report([])


def test_format_score_report_includes_grade():
    e = make_entry()
    scores = score_entries([e])
    out = format_score_report(scores)
    assert "[A]" in out or "[B]" in out or "[C]" in out


def test_format_score_report_top_n():
    entries = [make_entry(command=f"echo {i}") for i in range(10)]
    scores = score_entries(entries)
    out = format_score_report(scores, top_n=3)
    # Count entry rows (lines starting with '  [')
    rows = [l for l in out.splitlines() if l.strip().startswith("[")]
    assert len(rows) <= 3


def test_format_score_summary_empty():
    assert "No entries" in format_score_summary([])


def test_format_score_summary_shows_avg():
    entries = [make_entry(), make_entry(command="rm -rf /")]
    scores = score_entries(entries)
    out = format_score_summary(scores)
    assert "avg=" in out
    assert "Worst" in out


def test_format_scores_by_grade_empty():
    assert "No entries" in format_scores_by_grade([])


def test_format_scores_by_grade_groups_entries():
    entries = [make_entry(), make_entry(command="rm -rf / | bash")]
    scores = score_entries(entries)
    out = format_scores_by_grade(scores)
    assert "Grade" in out
