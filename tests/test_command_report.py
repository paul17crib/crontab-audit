"""Tests for crontab_audit.command_report."""

import pytest
from crontab_audit.parser import CrontabEntry
from crontab_audit.command_report import (
    format_command_stats,
    format_top_commands,
    format_commands_per_host,
)
from crontab_audit.command_stats import build_command_stats


def make_entry(command: str, host: str = "host1") -> CrontabEntry:
    return CrontabEntry(
        minute="0", hour="*", dom="*", month="*", dow="*",
        command=command, host=host, raw=f"0 * * * * {command}",
    )


def test_format_command_stats_empty():
    result = format_command_stats({})
    assert "No commands" in result


def test_format_command_stats_includes_command():
    entries = [make_entry("rsync -a /src"), make_entry("rsync -b /dst")]
    stats = build_command_stats(entries)
    result = format_command_stats(stats)
    assert "rsync" in result
    assert "2" in result


def test_format_command_stats_sorted_by_count():
    entries = [
        make_entry("rsync"),
        make_entry("rsync"),
        make_entry("python3"),
    ]
    stats = build_command_stats(entries)
    result = format_command_stats(stats)
    rsync_pos = result.index("rsync")
    python_pos = result.index("python3")
    assert rsync_pos < python_pos


def test_format_top_commands_empty():
    result = format_top_commands([])
    assert "No commands" in result


def test_format_top_commands_shows_rank():
    entries = [make_entry("rsync -a /src"), make_entry("rsync -a /src")]
    result = format_top_commands(entries, n=5)
    assert "1." in result
    assert "rsync" in result
    assert "x2" in result


def test_format_top_commands_respects_n():
    entries = [
        make_entry("rsync"),
        make_entry("python3"),
        make_entry("bash"),
    ]
    result = format_top_commands(entries, n=2)
    assert result.count(".") >= 2
    # Should not list more than n entries (each rank line has a dot)
    lines = [l for l in result.splitlines() if l.strip().startswith(("1.", "2.", "3."))]
    assert len(lines) <= 2


def test_format_commands_per_host_empty():
    result = format_commands_per_host([])
    assert "No entries" in result


def test_format_commands_per_host_shows_hosts():
    entries = [
        make_entry("rsync", "hostA"),
        make_entry("python3", "hostA"),
        make_entry("bash", "hostB"),
    ]
    result = format_commands_per_host(entries)
    assert "hostA" in result
    assert "hostB" in result
    assert "2" in result  # hostA has 2 commands
