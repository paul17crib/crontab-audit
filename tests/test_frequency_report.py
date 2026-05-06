"""Tests for frequency_report and frequency_cli modules."""

import argparse
from unittest.mock import patch, MagicMock

import pytest

from crontab_audit.parser import CrontabEntry
from crontab_audit.frequency_report import (
    group_by_frequency,
    format_frequency_group,
    format_frequency_report,
    format_frequency_summary,
)
from crontab_audit.frequency_cli import cmd_report, build_parser


def make_entry(minute="0", hour="*", dom="*", month="*", dow="*",
               command="/usr/bin/true", host="host1") -> CrontabEntry:
    e = CrontabEntry(
        minute=minute, hour=hour, dom=dom, month=month, dow=dow,
        command=command, raw=f"{minute} {hour} {dom} {month} {dow} {command}",
    )
    e.host = host
    return e


# --- group_by_frequency ---

def test_group_by_frequency_empty():
    assert group_by_frequency([]) == {}


def test_group_by_frequency_single_daily():
    entry = make_entry(minute="0", hour="6")
    groups = group_by_frequency([entry])
    assert "daily" in groups
    assert entry in groups["daily"]


def test_group_by_frequency_minutely():
    entry = make_entry(minute="*", hour="*")
    groups = group_by_frequency([entry])
    assert "minutely" in groups


def test_group_by_frequency_multiple_labels():
    daily = make_entry(minute="0", hour="3")
    minutely = make_entry(minute="*", hour="*", command="/bin/check")
    groups = group_by_frequency([daily, minutely])
    assert "daily" in groups
    assert "minutely" in groups


# --- format_frequency_group ---

def test_format_frequency_group_includes_label():
    entry = make_entry()
    result = format_frequency_group("daily", [entry])
    assert "[DAILY]" in result


def test_format_frequency_group_includes_command():
    entry = make_entry(command="/usr/bin/backup")
    result = format_frequency_group("daily", [entry])
    assert "/usr/bin/backup" in result


def test_format_frequency_group_includes_host():
    entry = make_entry(host="webserver")
    result = format_frequency_group("daily", [entry])
    assert "webserver" in result


def test_format_frequency_group_count():
    entries = [make_entry(), make_entry(command="/bin/foo")]
    result = format_frequency_group("hourly", entries)
    assert "(2 entries)" in result


# --- format_frequency_report ---

def test_format_frequency_report_empty():
    result = format_frequency_report([])
    assert "No entries" in result


def test_format_frequency_report_contains_section():
    entry = make_entry(minute="0", hour="4")
    result = format_frequency_report([entry])
    assert "[DAILY]" in result


def test_format_frequency_report_show_empty_includes_all_buckets():
    entry = make_entry(minute="0", hour="4")
    result = format_frequency_report([entry], show_empty=True)
    assert "[WEEKLY]" in result or "[MONTHLY]" in result


# --- format_frequency_summary ---

def test_format_frequency_summary_empty():
    result = format_frequency_summary([])
    assert "no entries" in result


def test_format_frequency_summary_includes_label():
    entry = make_entry(minute="0", hour="2")
    result = format_frequency_summary([entry])
    assert "daily=1" in result


# --- CLI ---

def test_build_parser_returns_parser():
    parser = build_parser()
    assert isinstance(parser, argparse.ArgumentParser)


def test_cmd_report_returns_0(tmp_path, capsys):
    cron_file = tmp_path / "host1.cron"
    cron_file.write_text("0 6 * * * /usr/bin/backup\n")
    args = argparse.Namespace(
        paths=[str(cron_file)],
        directory=False,
        summary=False,
        show_empty=False,
    )
    result = cmd_report(args)
    assert result == 0


def test_cmd_report_summary_flag(tmp_path, capsys):
    cron_file = tmp_path / "host1.cron"
    cron_file.write_text("* * * * * /bin/check\n")
    args = argparse.Namespace(
        paths=[str(cron_file)],
        directory=False,
        summary=True,
        show_empty=False,
    )
    cmd_report(args)
    captured = capsys.readouterr()
    assert "Frequency summary" in captured.out
