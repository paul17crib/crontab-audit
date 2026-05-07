"""Tests for label_classifier and label_report modules."""

import pytest
from crontab_audit.parser import CrontabEntry
from crontab_audit.label_classifier import (
    classify_entry,
    classify_entries,
    group_by_label,
    LabeledEntry,
)
from crontab_audit.label_report import (
    format_label_report,
    format_label_summary,
    format_unknown_entries,
)


def make_entry(command: str, host: str = "host1") -> CrontabEntry:
    e = CrontabEntry(
        minute="0", hour="2", dom="*", month="*", dow="*", command=command
    )
    e.host = host
    return e


def test_classify_backup_command():
    entry = make_entry("/usr/bin/pg_dump mydb > /backups/db.sql")
    result = classify_entry(entry)
    assert "backup" in result.labels


def test_classify_cleanup_command():
    entry = make_entry("find /tmp -mtime +7 -delete")
    result = classify_entry(entry)
    assert "cleanup" in result.labels


def test_classify_monitoring_command():
    entry = make_entry("/opt/scripts/healthcheck.sh")
    result = classify_entry(entry)
    assert "monitoring" in result.labels


def test_classify_unknown_command():
    entry = make_entry("/usr/local/bin/xyzzy_obscure_tool")
    result = classify_entry(entry)
    assert result.labels == []
    assert result.primary_label() is None


def test_classify_multiple_labels():
    entry = make_entry("rsync -av /data /backup && rm -rf /tmp/old")
    result = classify_entry(entry)
    assert "sync" in result.labels or "backup" in result.labels
    assert "cleanup" in result.labels


def test_primary_label_returns_first():
    entry = make_entry("/usr/bin/pg_dump mydb")
    result = classify_entry(entry)
    assert result.primary_label() == result.labels[0]


def test_classify_entries_returns_list():
    entries = [make_entry("pg_dump db"), make_entry("rm -rf /tmp/*")]
    results = classify_entries(entries)
    assert len(results) == 2
    assert all(isinstance(r, LabeledEntry) for r in results)


def test_group_by_label_groups_correctly():
    entries = [
        make_entry("pg_dump db"),
        make_entry("mysqldump db2"),
        make_entry("find /tmp -delete"),
    ]
    labeled = classify_entries(entries)
    groups = group_by_label(labeled)
    assert "backup" in groups
    assert len(groups["backup"]) == 2
    assert "cleanup" in groups


def test_group_by_label_unknown_key():
    entry = make_entry("/bin/xyzzy_unknown_cmd")
    labeled = [classify_entry(entry)]
    groups = group_by_label(labeled)
    assert "unknown" in groups


def test_format_label_report_empty():
    assert format_label_report([]) == "No entries to classify."


def test_format_label_report_includes_label():
    entry = make_entry("pg_dump mydb")
    labeled = classify_entries([entry])
    report = format_label_report(labeled)
    assert "BACKUP" in report or "backup" in report.lower()


def test_format_label_summary_includes_total():
    entries = [make_entry("pg_dump db"), make_entry("/bin/xyzzy")]
    labeled = classify_entries(entries)
    summary = format_label_summary(labeled)
    assert "TOTAL" in summary
    assert "2" in summary


def test_format_label_summary_empty():
    assert format_label_summary([]) == "No entries classified."


def test_format_unknown_entries_none_unknown():
    entry = make_entry("pg_dump db")
    labeled = classify_entries([entry])
    result = format_unknown_entries(labeled)
    assert "successfully classified" in result


def test_format_unknown_entries_lists_unknown():
    entry = make_entry("/bin/xyzzy_obscure", host="srv1")
    labeled = [classify_entry(entry)]
    result = format_unknown_entries(labeled)
    assert "srv1" in result
    assert "xyzzy_obscure" in result
