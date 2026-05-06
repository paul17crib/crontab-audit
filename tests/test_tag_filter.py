"""Tests for crontab_audit.tag_filter module."""

import pytest
from crontab_audit.parser import CrontabEntry
from crontab_audit.tag_filter import extract_tags, filter_by_tag, group_by_tag


def make_entry(command: str, host: str = "host1") -> CrontabEntry:
    entry = CrontabEntry(
        minute="0",
        hour="2",
        dom="*",
        month="*",
        dow="*",
        command=command,
        raw="0 2 * * * " + command,
        host=host,
    )
    return entry


def test_extract_tags_single():
    entry = make_entry("/usr/bin/backup.sh  # tags: backup")
    assert extract_tags(entry) == ["backup"]


def test_extract_tags_multiple():
    entry = make_entry("/usr/bin/deploy.sh  # tags: deploy, critical, prod")
    assert extract_tags(entry) == ["deploy", "critical", "prod"]


def test_extract_tags_no_tags():
    entry = make_entry("/usr/bin/simple.sh")
    assert extract_tags(entry) == []


def test_extract_tags_case_insensitive():
    entry = make_entry("/usr/bin/foo.sh  # Tags: Backup, CRITICAL")
    assert extract_tags(entry) == ["backup", "critical"]


def test_extract_tags_singular_keyword():
    entry = make_entry("/usr/bin/foo.sh  # tag: cleanup")
    assert extract_tags(entry) == ["cleanup"]


def test_filter_by_tag_any_match():
    entries = [
        make_entry("/bin/a.sh  # tags: backup"),
        make_entry("/bin/b.sh  # tags: deploy"),
        make_entry("/bin/c.sh  # tags: backup, deploy"),
        make_entry("/bin/d.sh"),
    ]
    result = filter_by_tag(entries, "backup")
    assert len(result) == 2
    assert all("backup" in e.command for e in result)


def test_filter_by_tag_require_all():
    entries = [
        make_entry("/bin/a.sh  # tags: backup"),
        make_entry("/bin/b.sh  # tags: backup, critical"),
        make_entry("/bin/c.sh  # tags: critical"),
    ]
    result = filter_by_tag(entries, "backup,critical", require_all=True)
    assert len(result) == 1
    assert "backup, critical" in result[0].command


def test_filter_by_tag_empty_tag_returns_all():
    entries = [
        make_entry("/bin/a.sh  # tags: backup"),
        make_entry("/bin/b.sh"),
    ]
    result = filter_by_tag(entries, "")
    assert result == entries


def test_filter_by_tag_no_match_returns_empty():
    entries = [
        make_entry("/bin/a.sh  # tags: backup"),
    ]
    result = filter_by_tag(entries, "nonexistent")
    assert result == []


def test_group_by_tag_basic():
    entries = [
        make_entry("/bin/a.sh  # tags: backup"),
        make_entry("/bin/b.sh  # tags: deploy"),
        make_entry("/bin/c.sh  # tags: backup, deploy"),
        make_entry("/bin/d.sh"),
    ]
    groups = group_by_tag(entries)
    assert len(groups["backup"]) == 2
    assert len(groups["deploy"]) == 2
    assert len(groups["__untagged__"]) == 1


def test_group_by_tag_all_untagged():
    entries = [make_entry("/bin/a.sh"), make_entry("/bin/b.sh")]
    groups = group_by_tag(entries)
    assert list(groups.keys()) == ["__untagged__"]
    assert len(groups["__untagged__"]) == 2


def test_group_by_tag_empty_list():
    groups = group_by_tag([])
    assert groups == {}
