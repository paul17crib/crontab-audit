"""Tests for entry_archiver and entry_archiver_report."""

import json
import os
import pytest

from crontab_audit.parser import CrontabEntry
from crontab_audit.entry_archiver import (
    ArchiveRecord,
    archive_entries,
    load_archive,
    filter_archive,
)
from crontab_audit.entry_archiver_report import (
    format_archive_records,
    format_archive_summary,
    format_archive_by_host,
)


def make_entry(
    command: str = "/usr/bin/backup.sh",
    host: str = "web01",
    user: str = "root",
    schedule: tuple = ("0", "2", "*", "*", "*"),
) -> CrontabEntry:
    return CrontabEntry(
        schedule_fields=list(schedule),
        command=command,
        host=host,
        user=user,
        raw_line=f"{' '.join(schedule)} {command}",
    )


def test_archive_record_to_dict():
    r = ArchiveRecord(archived_at="2024-01-01T00:00:00+00:00", host="h1", user="root", schedule="0 2 * * *", command="/bin/x")
    d = r.to_dict()
    assert d["host"] == "h1"
    assert d["command"] == "/bin/x"


def test_archive_record_from_dict_roundtrip():
    r = ArchiveRecord(archived_at="2024-01-01T00:00:00+00:00", host="h1", user="root", schedule="0 2 * * *", command="/bin/x")
    r2 = ArchiveRecord.from_dict(r.to_dict())
    assert r2.host == r.host
    assert r2.command == r.command


def test_archive_record_str_includes_host():
    r = ArchiveRecord(archived_at="2024-01-01T00:00:00+00:00", host="web01", user="root", schedule="* * * * *", command="/bin/y")
    assert "web01" in str(r)
    assert "/bin/y" in str(r)


def test_archive_entries_creates_file(tmp_path):
    path = str(tmp_path / "archive.json")
    entries = [make_entry()]
    records = archive_entries(entries, path, timestamp="2024-06-01T00:00:00+00:00")
    assert os.path.exists(path)
    assert len(records) == 1
    assert records[0].command == "/usr/bin/backup.sh"


def test_archive_entries_appends_on_second_call(tmp_path):
    path = str(tmp_path / "archive.json")
    archive_entries([make_entry("/bin/a")], path, timestamp="2024-01-01T00:00:00+00:00")
    archive_entries([make_entry("/bin/b")], path, timestamp="2024-01-02T00:00:00+00:00")
    with open(path) as fh:
        data = json.load(fh)
    assert len(data) == 2
    commands = {d["command"] for d in data}
    assert "/bin/a" in commands
    assert "/bin/b" in commands


def test_load_archive_returns_records(tmp_path):
    path = str(tmp_path / "archive.json")
    archive_entries([make_entry()], path, timestamp="2024-01-01T00:00:00+00:00")
    records = load_archive(path)
    assert len(records) == 1
    assert isinstance(records[0], ArchiveRecord)


def test_load_archive_missing_file_returns_empty(tmp_path):
    path = str(tmp_path / "nonexistent.json")
    assert load_archive(path) == []


def test_filter_archive_by_host():
    records = [
        ArchiveRecord("t", "web01", "root", "* * * * *", "/bin/a"),
        ArchiveRecord("t", "db01", "root", "* * * * *", "/bin/b"),
    ]
    result = filter_archive(records, host="web01")
    assert len(result) == 1
    assert result[0].command == "/bin/a"


def test_filter_archive_by_command_fragment():
    records = [
        ArchiveRecord("t", "web01", "root", "* * * * *", "/usr/bin/backup.sh"),
        ArchiveRecord("t", "web01", "root", "* * * * *", "/bin/cleanup.sh"),
    ]
    result = filter_archive(records, command_fragment="backup")
    assert len(result) == 1
    assert "backup" in result[0].command


def test_format_archive_records_empty():
    assert "No archived" in format_archive_records([])


def test_format_archive_records_includes_command():
    records = [ArchiveRecord("2024-01-01T00:00:00+00:00", "h", "u", "* * * * *", "/bin/test")]
    out = format_archive_records(records)
    assert "/bin/test" in out


def test_format_archive_summary_counts():
    records = [
        ArchiveRecord("2024-01-01T00:00:00+00:00", "h1", "u", "* * * * *", "/a"),
        ArchiveRecord("2024-01-02T00:00:00+00:00", "h2", "u", "* * * * *", "/b"),
    ]
    out = format_archive_summary(records)
    assert "2" in out


def test_format_archive_by_host_groups_correctly():
    records = [
        ArchiveRecord("t", "web01", "root", "* * * * *", "/bin/a"),
        ArchiveRecord("t", "db01", "root", "* * * * *", "/bin/b"),
    ]
    out = format_archive_by_host(records)
    assert "web01" in out
    assert "db01" in out
