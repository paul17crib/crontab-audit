"""Tests for crontab_audit.entry_search and entry_search_report."""
import pytest

from crontab_audit.parser import CrontabEntry
from crontab_audit.entry_search import (
    SearchResult,
    search_entries,
    search_by_command,
    search_by_host,
)
from crontab_audit.entry_search_report import (
    format_search_results,
    format_search_summary,
    format_results_by_host,
)


def make_entry(command: str, host: str = "host1", user: str = None) -> CrontabEntry:
    entry = CrontabEntry(
        minute="0",
        hour="2",
        dom="*",
        month="*",
        dow="*",
        command=command,
    )
    entry.host = host
    entry.user = user
    return entry


# --- search_entries ---

def test_search_entries_finds_match_in_command():
    entries = [make_entry("/usr/bin/backup.sh"), make_entry("/usr/bin/echo hello")]
    results = search_entries(entries, "backup")
    assert len(results) == 1
    assert results[0].entry.command == "/usr/bin/backup.sh"


def test_search_entries_case_insensitive_by_default():
    entries = [make_entry("/scripts/Backup.sh")]
    results = search_entries(entries, "backup")
    assert len(results) == 1


def test_search_entries_case_sensitive_no_match():
    entries = [make_entry("/scripts/Backup.sh")]
    results = search_entries(entries, "backup", case_sensitive=True)
    assert results == []


def test_search_entries_returns_empty_when_no_match():
    entries = [make_entry("echo hello")]
    results = search_entries(entries, "rsync")
    assert results == []


def test_search_entries_matches_host_field():
    e1 = make_entry("echo a", host="web-01")
    e2 = make_entry("echo b", host="db-01")
    results = search_entries([e1, e2], "web", fields=["host"])
    assert len(results) == 1
    assert "host" in results[0].matched_fields


def test_search_entries_matches_user_field():
    e = make_entry("echo a", user="deploy")
    results = search_entries([e], "deploy", fields=["user"])
    assert len(results) == 1
    assert "user" in results[0].matched_fields


def test_search_entries_invalid_regex_raises_value_error():
    with pytest.raises(ValueError, match="Invalid search query"):
        search_entries([make_entry("echo")], "[invalid")


def test_search_entries_snippet_highlights_match():
    entries = [make_entry("/scripts/backup.sh")]
    results = search_entries(entries, "backup")
    assert "<backup>" in results[0].snippet


def test_search_entries_multiple_field_matches_recorded():
    e = make_entry("backup", host="backup-host")
    results = search_entries([e], "backup", fields=["command", "host"])
    assert len(results) == 1
    assert "command" in results[0].matched_fields
    assert "host" in results[0].matched_fields


# --- convenience wrappers ---

def test_search_by_command_only_searches_command():
    e = make_entry("echo", host="rsync-host")
    results = search_by_command([e], "rsync")
    assert results == []


def test_search_by_host_finds_host():
    e = make_entry("echo", host="prod-01")
    results = search_by_host([e], "prod-01")
    assert len(results) == 1


# --- report formatting ---

def test_format_search_results_empty():
    assert format_search_results([]) == "No matching entries found."


def test_format_search_results_includes_snippet():
    e = make_entry("/scripts/backup.sh")
    r = SearchResult(entry=e, matched_fields=["command"], snippet="/scripts/<backup>.sh")
    output = format_search_results([r])
    assert "<backup>" in output


def test_format_search_results_verbose_shows_schedule():
    e = make_entry("echo")
    r = SearchResult(entry=e, matched_fields=["command"], snippet="echo")
    output = format_search_results([r], verbose=True)
    assert "schedule" in output


def test_format_search_summary_zero():
    assert "0" in format_search_summary([])


def test_format_search_summary_counts_hosts():
    e1 = make_entry("echo", host="h1")
    e2 = make_entry("echo", host="h2")
    r1 = SearchResult(entry=e1, matched_fields=["command"], snippet="echo")
    r2 = SearchResult(entry=e2, matched_fields=["command"], snippet="echo")
    summary = format_search_summary([r1, r2])
    assert "2 host" in summary


def test_format_results_by_host_groups_correctly():
    e1 = make_entry("echo", host="alpha")
    e2 = make_entry("rsync", host="beta")
    r1 = SearchResult(entry=e1, matched_fields=["command"], snippet="echo")
    r2 = SearchResult(entry=e2, matched_fields=["command"], snippet="rsync")
    output = format_results_by_host([r1, r2])
    assert "alpha" in output
    assert "beta" in output


def test_format_results_by_host_empty():
    assert "No matching" in format_results_by_host([])


def test_search_result_str_includes_host_and_command():
    e = make_entry("backup.sh", host="srv-01")
    r = SearchResult(entry=e, matched_fields=["command"], snippet="backup.sh")
    s = str(r)
    assert "srv-01" in s
    assert "backup.sh" in s
