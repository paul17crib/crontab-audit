"""Tests for crontab_audit.entry_stats."""
import pytest
from crontab_audit.parser import CrontabEntry
from crontab_audit.entry_stats import (
    EntryStats,
    _command_key,
    compute_entry_stats,
)


def make_entry(
    minute="0",
    hour="*",
    dom="*",
    month="*",
    dow="*",
    command="/usr/bin/true",
    user=None,
    host=None,
):
    return CrontabEntry(
        minute=minute,
        hour=hour,
        dom=dom,
        month=month,
        dow=dow,
        command=command,
        user=user,
        host=host,
    )


def test_compute_stats_empty_list():
    stats = compute_entry_stats([])
    assert stats.total_entries == 0
    assert stats.entries_with_user == 0
    assert stats.entries_with_host == 0
    assert stats.frequency_counts == {}
    assert stats.top_commands == []


def test_compute_stats_total_entries():
    entries = [make_entry(), make_entry(), make_entry()]
    stats = compute_entry_stats(entries)
    assert stats.total_entries == 3


def test_compute_stats_entries_with_user():
    entries = [
        make_entry(user="root"),
        make_entry(user=None),
        make_entry(user="deploy"),
    ]
    stats = compute_entry_stats(entries)
    assert stats.entries_with_user == 2


def test_compute_stats_entries_with_host():
    entries = [
        make_entry(host="web01"),
        make_entry(host=None),
    ]
    stats = compute_entry_stats(entries)
    assert stats.entries_with_host == 1


def test_compute_stats_frequency_counts_present():
    entries = [
        make_entry(minute="*", hour="*"),   # minutely
        make_entry(minute="0", hour="*"),   # hourly
        make_entry(minute="0", hour="0"),   # daily
    ]
    stats = compute_entry_stats(entries)
    assert isinstance(stats.frequency_counts, dict)
    assert sum(stats.frequency_counts.values()) == 3


def test_compute_stats_top_commands_sorted():
    entries = [
        make_entry(command="/bin/backup"),
        make_entry(command="/bin/backup"),
        make_entry(command="/bin/cleanup"),
    ]
    stats = compute_entry_stats(entries)
    assert stats.top_commands[0][0] == "/bin/backup"
    assert stats.top_commands[0][1] == 2


def test_command_key_simple_path():
    entry = make_entry(command="/usr/bin/rsync -avz /src /dst")
    assert _command_key(entry) == "/usr/bin/rsync"


def test_command_key_bare_word():
    entry = make_entry(command="backup")
    assert _command_key(entry) == "backup"


def test_command_key_env_prefix_skipped():
    entry = make_entry(command="HOME=/root /usr/bin/python script.py")
    assert _command_key(entry) == "/usr/bin/python"


def test_command_key_empty_command():
    entry = make_entry(command="")
    assert _command_key(entry) == ""


def test_str_output_contains_total():
    entries = [make_entry(user="root", host="srv1")]
    stats = compute_entry_stats(entries)
    text = str(stats)
    assert "Total entries" in text
    assert "1" in text


def test_host_counts_populated():
    entries = [
        make_entry(host="web01"),
        make_entry(host="web01"),
        make_entry(host="db01"),
    ]
    stats = compute_entry_stats(entries)
    assert stats.host_counts["web01"] == 2
    assert stats.host_counts["db01"] == 1


def test_user_counts_populated():
    entries = [
        make_entry(user="root"),
        make_entry(user="root"),
        make_entry(user="nobody"),
    ]
    stats = compute_entry_stats(entries)
    assert stats.user_counts["root"] == 2
    assert stats.user_counts["nobody"] == 1
