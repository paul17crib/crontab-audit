"""Tests for entry_filter, entry_filter_report, and entry_filter_cli."""

from __future__ import annotations

import argparse
from unittest.mock import patch, MagicMock

from crontab_audit.parser import CrontabEntry
from crontab_audit.entry_filter import (
    EntryFilter,
    apply_filter,
    filter_by_host,
    filter_by_command,
    filter_by_user,
)
from crontab_audit.entry_filter_report import (
    format_filter_criteria,
    format_filtered_entries,
    format_filter_summary,
)
from crontab_audit.entry_filter_cli import build_parser, cmd_filter


def make_entry(command="/usr/bin/backup", minute="0", hour="2", host="host1", user="root"):
    e = CrontabEntry(
        schedule_fields=[minute, hour, "*", "*", "*"],
        command=command,
        raw_line=f"{minute} {hour} * * * {command}",
    )
    e.host = host
    e.user = user
    return e


# --- EntryFilter.matches ---

def test_filter_matches_all_when_no_criteria():
    entries = [make_entry(), make_entry(command="/bin/echo hello")]
    f = EntryFilter()
    assert apply_filter(entries, f) == entries


def test_filter_by_host_matches():
    e1 = make_entry(host="web1")
    e2 = make_entry(host="db1")
    result = filter_by_host([e1, e2], "web1")
    assert result == [e1]


def test_filter_by_user_matches():
    e1 = make_entry(user="deploy")
    e2 = make_entry(user="root")
    result = filter_by_user([e1, e2], "deploy")
    assert result == [e1]


def test_filter_by_command_pattern():
    e1 = make_entry(command="/usr/bin/rsync -av /src /dst")
    e2 = make_entry(command="/bin/echo hello")
    result = filter_by_command([e1, e2], r"rsync")
    assert result == [e1]


def test_filter_by_minute():
    e1 = make_entry(minute="5")
    e2 = make_entry(minute="0")
    f = EntryFilter(minute="5")
    assert apply_filter([e1, e2], f) == [e1]


def test_filter_by_hour():
    e1 = make_entry(hour="3")
    e2 = make_entry(hour="12")
    f = EntryFilter(hour="3")
    assert apply_filter([e1, e2], f) == [e1]


def test_filter_combined_criteria():
    e1 = make_entry(host="web1", user="root", command="/usr/bin/backup")
    e2 = make_entry(host="web1", user="deploy", command="/usr/bin/backup")
    f = EntryFilter(host="web1", user="root")
    assert apply_filter([e1, e2], f) == [e1]


# --- format helpers ---

def test_format_filter_criteria_none():
    out = format_filter_criteria(EntryFilter())
    assert "(none)" in out


def test_format_filter_criteria_with_host():
    out = format_filter_criteria(EntryFilter(host="web1"))
    assert "host=web1" in out


def test_format_filtered_entries_empty():
    out = format_filtered_entries([], EntryFilter())
    assert "No entries" in out


def test_format_filtered_entries_lists_entries():
    e = make_entry(command="/bin/backup", host="srv1")
    out = format_filtered_entries([e], EntryFilter())
    assert "/bin/backup" in out
    assert "srv1" in out


def test_format_filter_summary_percentage():
    out = format_filter_summary(10, 5)
    assert "5/10" in out
    assert "50.0%" in out


def test_format_filter_summary_zero_total():
    out = format_filter_summary(0, 0)
    assert "0/0" in out


# --- CLI ---

def test_build_parser_returns_parser():
    p = build_parser()
    assert isinstance(p, argparse.ArgumentParser)


def test_cmd_filter_returns_1_when_no_matches(tmp_path):
    cron_file = tmp_path / "host1.cron"
    cron_file.write_text("0 2 * * * /bin/backup\n")
    args = argparse.Namespace(
        path=str(cron_file),
        host="nonexistent",
        user=None,
        command=None,
        minute=None,
        hour=None,
        tag=None,
    )
    result = cmd_filter(args)
    assert result == 1


def test_cmd_filter_returns_0_when_matched(tmp_path):
    cron_file = tmp_path / "host1.cron"
    cron_file.write_text("0 2 * * * /bin/backup\n")
    args = argparse.Namespace(
        path=str(cron_file),
        host=None,
        user=None,
        command="backup",
        minute=None,
        hour=None,
        tag=None,
    )
    result = cmd_filter(args)
    assert result == 0
