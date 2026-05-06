"""Tests for crontab_audit.stale_detector."""

import pytest
from crontab_audit.parser import CrontabEntry
from crontab_audit.stale_detector import (
    StalenessIssue,
    find_stale_entries,
    _command_suggests_stale,
    _comment_suggests_stale,
)


def make_entry(command: str, lineno: int = 1, host: str = "host1") -> CrontabEntry:
    return CrontabEntry(
        minute="0",
        hour="2",
        dom="*",
        month="*",
        dow="*",
        command=command,
        lineno=lineno,
        host=host,
    )


def test_command_suggests_stale_tmp_path():
    assert "/tmp/" in _command_suggests_stale("/tmp/run_job.sh")


def test_command_suggests_stale_deprecated_keyword():
    assert "deprecated" in _command_suggests_stale("/opt/deprecated_script.sh")


def test_command_suggests_stale_no_match():
    assert _command_suggests_stale("/usr/bin/clean_logs.sh") == []


def test_comment_suggests_stale_deprecated():
    assert "deprecated" in _comment_suggests_stale("deprecated since 2021")


def test_comment_suggests_stale_todo():
    assert "todo" in _comment_suggests_stale("TODO: remove this")


def test_comment_suggests_stale_no_match():
    assert _comment_suggests_stale("runs nightly backup") == []


def test_find_stale_entries_detects_tmp_command():
    entries = [make_entry("/tmp/nightly.sh")]
    issues = find_stale_entries(entries)
    assert len(issues) == 1
    assert issues[0].severity == "warning"
    assert "/tmp/" in issues[0].reason


def test_find_stale_entries_detects_disabled_in_path():
    entries = [make_entry("/opt/scripts/DISABLED_backup.sh")]
    issues = find_stale_entries(entries)
    assert len(issues) == 1
    assert "DISABLED" in issues[0].reason


def test_find_stale_entries_inline_comment_deprecated():
    entries = [make_entry("/usr/bin/report.sh # deprecated")
    ]
    issues = find_stale_entries(entries)
    assert len(issues) == 1
    assert issues[0].severity == "info"
    assert "deprecated" in issues[0].reason


def test_find_stale_entries_inline_comment_fixme():
    entries = [make_entry("/usr/bin/sync.sh # FIXME: remove after migration")]
    issues = find_stale_entries(entries)
    assert len(issues) == 1
    assert "fixme" in issues[0].reason


def test_find_stale_entries_safe_command_no_issues():
    entries = [make_entry("/usr/bin/clean_logs.sh")]
    issues = find_stale_entries(entries)
    assert issues == []


def test_find_stale_entries_multiple_entries_mixed():
    entries = [
        make_entry("/usr/bin/report.sh", lineno=1),
        make_entry("/tmp/old_job.sh", lineno=2),
        make_entry("/opt/nightly.sh # legacy", lineno=3),
    ]
    issues = find_stale_entries(entries)
    assert len(issues) == 2
    line_numbers = {i.entry.lineno for i in issues}
    assert 2 in line_numbers
    assert 3 in line_numbers


def test_staleness_issue_str_includes_host_and_reason():
    entry = make_entry("/tmp/test.sh", lineno=5, host="webserver")
    issue = StalenessIssue(entry=entry, reason="command contains stale indicator(s): ['/tmp/']", severity="warning")
    result = str(issue)
    assert "webserver" in result
    assert "line 5" in result
    assert "warning" in result.lower()


def test_staleness_issue_str_no_host():
    entry = make_entry("/tmp/test.sh", lineno=1, host="")
    issue = StalenessIssue(entry=entry, reason="stale", severity="info")
    result = str(issue)
    assert "[" not in result
